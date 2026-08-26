# Dream-State Learning

Research project: **experiential parametric memory for continual LLM agents** —
an agent's lived experience is consolidated ("dreamed") into adapter weights,
and we measure whether that memory keeps improving with experience where
retrieval and long context flatten. Target: ICLR 2027.

## Start here (live documents, in reading order)
- [`research_notes/00_THESIS.md`](research_notes/00_THESIS.md) — **the
  consolidated theory**: thesis, scaling ideology, architecture organs,
  measurement inventions, game doctrine. Read this before anything.
- [`SPEC_V2.md`](SPEC_V2.md) — the experiment: one-page overview (Part I) +
  full sizing pre-registration, sweeps, falsifier, parameter ledger (Part II).
- [`REVIEW_PACK.md`](REVIEW_PACK.md) — the system as built, written for
  verification: the three files that decide everything, reference numbers,
  play-it-yourself samples, current results state.
- [`DESIGN_SUPER.md`](DESIGN_SUPER.md) — the full architecture vision the
  experiment is the first slice of (engine, felt attention, dream,
  person-hierarchy, escalation ladders).
- [`research_notes/35_goalposts_paper1.md`](research_notes/35_goalposts_paper1.md)
  — **THE GOALPOSTS**: Paper 1 claim, the four-arm honesty ladder, the
  allowed/forbidden (cheating) line, C3loop, success criteria, deferred
  work. Check any new experiment against this.
- [`research_notes/`](research_notes/) — decision history; `32_*` is the
  running v2 design log, `33_*` the frozen Semantic World v0 contract,
  `25_*` the competitive-landscape audits.

## Live code
- [`alchemy/`](alchemy/) — the v2 pipeline: `world.py` (latent compositional
  environment), `env.py` (episodes/lives), `dreamer.py` (dream corpora +
  exposure augmentation), `lora_mem.py` (consolidation), `evals.py` +
  `run_v2.py` (the 7-arm × 7-checkpoint experiment), `report.py`
  (results → tables; the only source of reported numbers), `sizing_mc.py`
  (ceiling instrument), `run_smoke.py` (plumbing test).
- [`lands/`](lands/) — CPU-only prior-anchored LANDS instrument: deterministic
  hierarchical generator, aligned/neutral/conflicting skins, D0-D3 proof
  graphs, evidence-budgeted verifier, priced reachout, oracle/full-lifetime/
  context baselines, and checksummed artifact export.  It is the next-world
  interface for the proven G-series dream + read-only adapter stack.
- [`lands/`](lands/) — the Semantic World v0 instrument (Candyland/
  Blendyland; three isomorphic skins, D0–D3 proof-graded goals, claim
  grammar + verification entitlement, priced reachout). Start at
  `lands/HANDOFF_FABLE.md` (C0–C5 GPU ladder);
  spec: `research_notes/34_semantic_world_v0_spec.md`; measured GPU
  constraints: `research_notes/33_semantic_world_gpu_constraints.md`.
- [`gpu/`](gpu/) — node operations: `scout.py` (Colossus inventory search),
  `v2_bootstrap.sh` + `V2_NODE_SETUP.md` (worker setup incl. the GH200/ARM
  recipe), `v2node_*.sh` / `gh200_ssh.sh` (active-node wrappers).
- `paper/` — draft (prose written by Rohin, not generated).

## Archive (superseded, kept for provenance — do not build on)
- [`archive/session1/`](archive/session1/) — the session-1 program (June–Aug
  2026): felt-head + fast-weight benchmark (`felt/`, `game/`,
  `structmem_bench/`, the S1–S4 GPU pipeline under `gpu/`, and its spec/design
  docs). Its results and honest negatives are summarized in
  `research_notes/` (notes ≤31) and fed the v2 design; the code is frozen.
- [`archive/`](archive/) (root) — pre-session-1 scaffolding.
- `gpu_artifacts_local/` — untracked local backup of session-1 run artifacts
  (~1.8GB; gitignored).

## Working rules
- Every reported number comes from a script in this repo (usually
  `alchemy/report.py`). No hand-quoted results.
- Pre-registered gates and the falsifier live in `SPEC_V2.md` §7 and are
  checked before any claim.
