# TMEM as the shoulder we stand on — positioning for the paper (2026-09-10)

Source: Ren et al., "TMEM: Scaling Self-Evolving Agents via Parametric Memory" (arXiv 2606.04536, June 2026). Deep read: `16_tmem_deepread.md`; neighbours: `20260906_experience_learning_neighbors.md`.

## What TMEM established (we build on it, and say so on page 1)
- Frozen base θ0 + fast LoRA weights Δt updated online from self-extracted supervision; actions sampled from π(θ0+Δt). The extraction policy is RL-optimizable. SVD-based initialization of the LoRA subspace speeds online convergence.
- Result: LoRA fast weights can hold an agent's experience and change its behaviour within a single episode, beating summary- and retrieval-based memory on LoCoMo, LongMemEval-S, multi-objective search and CL-Bench.
- Its opening critique is our framing almost verbatim (prompt-space memory can look up but not learn from experience).

## The delta (state it, do not imply it)
| axis | TMEM | this paper |
|---|---|---|
| timescale | within one episode (fast-weight rollout dynamics) | across a lifetime: 1,024 episodes, a write every 32, up to 32 writes per life |
| write | online update from extracted QA-style supervision, extraction policy trained by RL | offline "sleep": the agent's own success-filtered continuations, retrained from the frozen model, committed only through gates (format canary; score and behaviour gates) |
| read | retrieval/QA-shaped; memory consulted per step | long thinking with markers; RECALL is keyword retrieval over the life ledger; the brief written at sleep opens the next wake |
| evaluation regime | retrieval benchmarks (LoCoMo, LongMemEval-S) plus search and CL-Bench | paired adapter-ON/OFF probes on a fixed panel at every checkpoint across the life; full-life harm counts; ritual (diversity-collapse) detection; per-life tables |
| failure studied | not studied | late-life behavioural collapse invisible to a format canary (4/9 ungated lives); recipe lock-in as what the write actually learns |
| development | none (no teacher) | parenting studied as an intervention (observational, not established) and a developmental pipeline proposed (bootstrap → parent → autonomy) |

One-paragraph version for the introduction (first page):
"TMEM (Ren et al., 2026) showed that an agent can absorb its own extracted experience into fast LoRA weights over a frozen base and act better within the same episode, and that the extraction policy can be trained; this established that per-agent parametric memory is feasible. We take the next step in timescale and regime: one agent writing a small personal adapter from its own gated continuations every 32 episodes for a 1,024-episode life, measured with paired adapter-on/off probes at every checkpoint and a full-life harm count. TMEM's evaluations are retrieval-shaped and within-episode; ours ask what such a write learns over a lifetime that no context window holds, how it fails, and what a behavioural gate can catch. We do not claim the developmental result (an agent taught to learn better, measured as a higher rate of improvement on novel tasks); we state it as the question this line of work is for."

## What we may NOT claim relative to TMEM
- That our write is better than TMEM's (no shared benchmark; different regimes).
- That parenting produces a better learner (not established; 1/3 parented lives had a harmful pair vs 4/9 controls; classroom arms did not separate).
- That the adapter stores usable knowledge (storage ≠ extraction is a reading).
- The killer result — d(performance)/d(experience) higher for the developed agent on novel task distributions — is the target of the programme, not a result of this paper.

## Worth stealing
- SVD-based LoRA subspace initialization (faster online convergence) — a free speedup to test for the sleep write; log as an ALIVE idea with a trigger (when the write's convergence time matters, i.e. sleep cost becomes the bottleneck).

## Rohin's framing to carry into the Discussion (2026-09-10)
Three timescales: parent-guided development → autonomous metacognitive learning → ordinary task execution. The learner's loop: experience → reason about experience → identify a reusable abstraction → test it → decide what becomes plastic → ΔLoRA → observe behavioural change → reason again; the metacognition itself should improve over development. TMEM learns from experience; this agent is being taught how to learn from experience. The parent is an outer-loop agent optimizing another agent's developmental trajectory, with scaffolding removed over time and the parent absent at deployment. Long-run: when thoughts saturate the LoRA, post-train the base.
