# Redteam 7 — GPU-tier scripts (unattended 48h A100 lease)

Scope: gpu/setup_node.sh, run_gates.py, rollouts.py, train_head_real.py,
probe_eval_real.py, RUNBOOK.md, felt/llm_player.py (HFBackend), felt/gates.py.
Method: full read, CPU probes (including an end-to-end S1→S2→S3 dry run on a
fake `gpu_artifacts/s1` built with MockTextPlayer in the exact rollouts schema),
and web verification of external facts. Date: 2026-08-11 (lease starts 8 AM).

---

## RANKED FINDINGS

### P0-1. FeltHead trains on RAW hidden states — saturation can fake a STOP at hour 12
`train_head_real.py` feeds real hidden states straight into `FeltHead`
(`head.py`): `z = (H @ Wk) @ q / √dk + b` with `Wk, q ~ N(0, 0.2)`. Mock
embeds are unit-norm; real last-layer LLM states are not normalized anywhere,
and Qwen-family states carry massive-activation dims (row norms 10²–10³).
CPU probe (d_h=1536, lr=0.02, 30 epochs, identical data at different scales,
sparse TD-like targets):

| state scale (row norm) | held-out regret after training |
|---|---|
| ~1 (mock-like) | 0.069 |
| ~39 | 0.069 (same, converges) |
| ~1160 | 0.282 (stalls — sigmoid saturated at init, `a(1-a)≈0`) |
| ~3900 | 0.313 |

No NaN/divergence (the ±30 clip holds), but training *stalls*, and the stalled
regret (~0.28) is far above the 0.15 STOP threshold. **The hour-12 kill-switch
can fire not because real states lack the salience signal, but because the head
undertrained at that scale — an irreversible wrong turn for the lease.**

**Minimal fix** (train_head_real.py + probe_eval_real.py, must be paired):
```python
# train_head_real.py, after building train/test:
scale = float(np.mean([np.linalg.norm(e["H"], axis=1).mean() for e in train]))
for e in train + test:
    e["H"] = e["H"] / scale
...
np.savez(a.out, ..., state_scale=scale)   # persist it

# probe_eval_real.py load_head(): return scale too; build_world_stream(): H /= scale
```
A global scalar preserves all relative structure (dividing by a constant), so it
cannot hurt; if regret is still high, per-feature z-scoring (also persisted) is
the next fallback before believing STOP.

### P0-2. PASS B npz checkpointing: non-atomic overwrite + O(n²) rewrite + full-RAM dict
`rollouts.py cache_states()`:
- `np.savez(cache_path, **cached)` **overwrites the live cache in place**. A
  kill/OOM mid-save corrupts `states.npz` → ALL PASS B progress lost, S2/S3
  blocked. On an unattended box this is the single most expensive corruption.
- Checkpoint every 20 batches re-serializes the FULL archive. Cost model at 10k
  episodes (~600k unique texts × 3 layers × 1536 f32): **~10.3 GB in RAM, ~10 GB
  per save, ~469 saves ≈ 2.4 TB of disk writes** — hours of pure I/O. At 2k
  episodes ~2 GB / ~190 GB writes: survivable but wasteful.
- `cached = {k: z[k] for k in z.files}` materializes the whole archive on resume.

**Minimal fix:**
```python
tmp = cache_path.with_suffix(".npz.tmp")
np.savez(tmp, **cached); os.replace(tmp, cache_path)      # atomic
if (i // batch_size) % 200 == 0:                          # 10x fewer checkpoints
```
(Nicer at 10k scale: shard files `states_0000.npz` per ~50k texts, never
rewritten; readers glob-merge. But atomic+less-frequent is the 3-line version.)

### P0-3. A truncated trailing JSONL line bricks resume AND all downstream stages
Rollouts are appended per episode with periodic flush; a crash/kill mid-write
leaves a partial last line. Probe confirmed: `json.loads` then raises
`JSONDecodeError` in **four** places — PASS A resume (`done_eps`), PASS B text
collection, S2 `load_episodes`, S3 `main`. One crash → every later stage dies
until a human edits the file. Unattended, that's the rest of the night.

**Minimal fix** — one tolerant reader used by all four:
```python
def iter_jsonl(path):
    seen = set()
    for ln in open(path):
        try: rec = json.loads(ln)
        except json.JSONDecodeError: continue   # truncated tail from a crash
        if rec["episode_uid"] in seen: continue  # dedupe re-run overlaps
        seen.add(rec["episode_uid"]); yield rec
```
(Dedupe matters: after skipping a truncated line, resume legitimately re-appends
that episode → without dedupe S2/S3 double-count it.)

### P1-4. setup_node.sh test gate is decorative — failing tests cannot stop setup
The three test files print `FAIL ...` but **always `exit 0`** (verified: the
`__main__` runners catch every exception). Combined with `2>/dev/null | tail -1`
(pipeline status = tail's; stderr discarded), a broken repo sails straight into
model downloads and GPU spend despite the "must be 50/50" comment. `set -e`
never fires.
**Minimal fix:**
```bash
for t in structmem game felt; do
    out=$(PYTHONPATH=. python tests/test_$t.py 2>&1 | tail -1)
    echo "  test_$t: $out"
    [[ "$out" == *"passed"* && "$out" != 0/* ]] || { echo "TESTS FAILED"; exit 1; }
done
```
(or add `sys.exit(1 if ok < len(fns) else 0)` to the three runners).
Current status for the record: 50/50 pass locally (27+9+14).

### P1-5. RUNBOOK `conda activate felt` fails in every fresh shell
Miniconda is installed with `-b` (no `conda init`), and setup_node.sh only
`eval`s the hook inside its own process. Hour 1–2's `conda activate felt` in a
new tmux/ssh shell → `conda: command not found`. Unattended-adjacent trap after
every reconnect.
**Minimal fix:** add to setup phase 2 after install:
`"$HOME/miniconda3/bin/conda" init bash` — or change RUNBOOK to
`eval "$($HOME/miniconda3/bin/conda shell.bash hook)" && conda activate felt`.

### P1-6. S0 gates: timing off by 2–5×, and raw prompts may under-measure win@manual
- Docstring says "~300 episodes ≈ 30–60 min"; defaults give **60 episodes**
  (3 worlds × 10 eps × 2 modes). But generation is *sequential single-prompt HF*
  (`HFBackend.generate`, 24 new tokens, ~500–900-token prompts) and every
  `none`-mode episode runs the full 60 steps (it can't win) → ~4.5–6k generate
  calls ≈ 1–3 h on the A100, blowing the hour-1–2 slot. Not fatal (plan slack or
  port S0 to vLLM later); know it going in.
- Neither `HFBackend` nor PASS A applies the model's **chat template** —
  Qwen2.5-*Instruct* on raw completions can fail the 0.85 gate for format
  reasons alone, triggering an unnecessary (paid) escalation to 3B. The RUNBOOK
  already allows "prompt iteration": make *apply chat template* iteration #1,
  and apply it identically in S0 and S1 (they're consistent today — keep them
  consistent after any change).

### P2-7. HF_TOKEN hard assert can stall phase 2 for no reason
All three models (Qwen2.5-1.5B/3B-Instruct, Phi-3.5-mini-instruct) are ungated;
Phi-3.5-mini confirmed public/MIT. `assert tok` turns a forgotten export into a
dead setup. Fix: `snapshot_download(m, token=tok or None)` and drop the assert
(keep a warning).

### P2-8. Open-ended pins on a paid lease: `vllm>=0.6`, `transformers>=4.45`
pip will take the latest vllm (2026) + whatever transformers resolves that
morning. A100 (sm_80) is supported by current vLLM and its pinned torch, and
the `torch.cuda.is_available()` gate catches gross breakage — but a same-week
bad vllm/transformers release becomes YOUR outage at hour 0. Minimal fix: pin
exact versions known-good the day before (e.g. `vllm==X.Y.Z transformers==A.B.C`
tested in a local venv for importability). `huggingface_hub` is a hard dep of
both vllm and transformers → importable after that pip line (verified concern:
none).

### P2-9. rollouts.py exposes no --seed/--n-worlds/--depth/--context-mode
Resume determinism (uid → world/goal/episode_seed) holds precisely BECAUSE
these are frozen defaults. Fine for the frozen plan; if anyone adds the flags
later, changing them mid-log silently corrupts the resume mapping. Add a
one-line comment in `run_rollouts` noting this invariant.

### P2-10. Minor consistency notes (no action required)
- PASS B `max_length=256` is ample: max observed event text = 191 chars
  (~<70 tokens; longest is the `inspect` obs). `HFBackend.get_event_states`
  uses 512 — harmless inconsistency, unify when S4 is wired.
- `probe_eval_real.py`: `world_seeds = {}` is dead code; `np.mean([])` → nan
  (+warning) if a policy ends with zero worlds — cosmetic.
- `play_episode` duplicates "Your goal: craft X." in the step-0 obs (reset
  already includes it) — S0-only cosmetic; PASS A builds its own obs correctly.

---

## VERIFIED GOOD (checked, no issue)
- **vLLM `LLM.generate(list)` preserves input order** (docs: outputs returned
  "in the same order as the input prompts") — the `zip(active, outs)` in PASS A
  is sound; early-finishing episodes are correctly dropped from `active` and
  every batch member is logged exactly once after the batch drains.
- **PASS A resume determinism**: uid=f(ep), world=`ep % n_worlds`,
  goal=`(ep//n_worlds) % len(goals)` with `list(world.dag.recipes)` ordering
  fixed by the world seed, `episode_seed=ep` — identical assignment across
  reruns and when scaling 2k→10k.
- **PASS B padding fix present**: `tok.padding_side = "right"` before
  last-non-pad indexing (`attention_mask.sum(1)-1`) — correct.
- **world_seed + depth are logged per record and used by S3**
  (`World.generate(wid, seed=recs[0]["world_seed"], depth=recs[0].get("depth",4))`,
  other generate kwargs are defaults on both sides) — regeneration is exact.
- **Kill-switch thresholds match IMPLEMENTATION_SPEC §5b**: proceed ≤ 3×0.03 =
  0.09, STOP ≥ 0.15, gray zone in between; `--layer` choices match cached
  LAYERS (-1,-4,-8); RUNBOOK commands match all script defaults/paths
  (s1 dir, s2_head.npz, s3_probe.json).
- **S3 end-to-end dry run on CPU passed**: `felt.baselines` private imports
  (`_weights, _fact_key, _fact_val, _floor_corrected_probe`) all exist;
  `dmem_style` path fine; step<1 / missing-state-key guards work; paired
  arrays stay aligned across policies (the detail-pool skip is policy-
  independent per world). `np.random.Generator.shuffle` on a Python list (S2)
  works.
- **`sudo ubuntu-drivers install` is valid 24.04 syntax**, and the fallback
  `nvidia-driver-570-server` (570.211.01) exists in noble; phase-1/phase-2
  gating via nvidia-smi is idempotent across the reboot; phase 2 rerun is
  idempotent (guarded conda create, guarded clone + pull, HF cache).
- **Repo reachability**: local repo IS a git repo, clean, HEAD == origin/main
  (867a107), and unauthenticated HTTPS ls-remote succeeds → the node's
  `git clone`/`git pull` flow works ("Claude ships fixes from the Mac" is
  operable).
- Salience/fact index alignment (`sal[fa.step-1]` ↔ trajectory) consistent with
  `felt/baselines.collect_stream`; `trajectory` records carry `salience` (oracle
  TD) as S2 requires; text keys (`action + ' ' + obs`, md5) identical across
  PASS B / S2 / S3.

## SUGGESTED PRE-LEASE PATCH ORDER (all CPU-testable tonight)
1. P0-1 state-scale normalization (train_head_real + probe_eval_real, persisted
   in s2_head.npz) — re-run the fake-s1 dry run after.
2. P0-3 tolerant `iter_jsonl` + uid dedupe in the four readers.
3. P0-2 atomic npz save + checkpoint every 200 batches.
4. P1-4 real test gate in setup_node.sh; P1-5 `conda init bash`.
5. P2-7 token-optional downloads; P2-8 pin exact vllm/transformers versions.
6. Push to origin/main so the node clones the fixed tree.

Sources: [vLLM LLM class docs (output order)](https://docs.vllm.ai/en/v0.6.3.post1/dev/offline_inference/llm.html), [nvidia-graphics-drivers-570-server in noble](https://launchpad.net/ubuntu/noble/+source/nvidia-graphics-drivers-570-server), [Phi-3.5-mini-instruct (public, MIT)](https://huggingface.co/microsoft/Phi-3.5-mini-instruct), [vLLM GPU installation docs](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/)
