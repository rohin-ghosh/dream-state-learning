# Legacy-A routine replication and OFF-noise terminal audit

**Date:** 2026-09-13 UTC
**Scope:** read-only audit of the twelve `A` reruns and the six standalone
OFF-noise jobs. No builder source, adapter, job, threshold, GPU state, or claim
gate was changed.

## Bottom line

Legacy cell A reliably writes a **life-specific action habit**. It does not
provide evidence of connected experiential knowledge or program-sensitive
memory. The rerun is stronger evidence for a behavioural attractor than prior
summaries stated, but the attractor is not literally one identical routine:
different lives preserve different suffixes after the common four-pass prefix.

The OFF sweep also changes the measurement reading. The report panel has an
empirical per-panel SD of `.00560`, while the disjoint panel has SD `.01145` in
this sweep. A generation seed produces a real disjoint-panel outlier, and exact
per-request seeds do not remove run-history effects. The disjoint panel is
therefore not intrinsically the quieter panel, and the current two-rep helper
must not be described as exact common-random pairing.

## Terminal and raw-score closure

At 02:17--02:18 UTC, the node-1 queue reported `running=0, done=29` and the
node-2 queue `running=0, done=58`. All seven relevant queue wrappers had an
exit receipt of `0`, and every recorded wrapper PID was absent:

- node 1: `fable_fill_pretest_R3_B_seed501_Arep`,
  `fable_fill_offnoise_n1_s6262`, `..._s7272`, and `..._s4242rep2`;
- node 2: `fable_fill_offnoise_n2_s6262`, `..._s7272`, and
  `..._s4242rep2`.

I recomputed every terminal panel mean from the raw `kind=act` rows: maximum
executed score per registered episode, with zero for an episode with no action,
then the panel average. All **72/72** means (48 A means and 24 OFF-noise means)
match the stored summaries; maximum absolute floating-point difference is
`1.11e-16`.

## What the A rerun actually varies

This is not an identical-adapter generation-seed rerun. For every one of the
twelve selected lives:

1. the old and new legacy corpus files are byte-identical;
2. `train_adapter.py` is run again with the legacy unseeded v1 recipe; and
3. the resulting old/new adapter weight hashes differ in **12/12** lives;
4. generation changes from base seed `4242` to `5252` (each file's second
   replicate adds `1000`).

Thus the rerun jointly tests retraining variability and generation-seed
variability. It cannot attribute any difference to one of them. The identical
per-life corpus is the fixed treatment.

Despite both perturbations, the dominant first action from each life is
identical old versus new in **48/48** corresponding panel/replicate cells. In
the new raw ledgers, its modal share has mean `.9265`, median `1.0`, is at least
`.75` in **44/48** cells, and is exactly `1.0` in **30/48**. Across all
program-by-replicate best-score cells, **400/480** are numerically identical
old versus new. Eight of twelve lives change by less than `.005` on both panel
means; eleven of twelve change by less than `.01`. The exception is
`R2_B_seed5`, whose report mean falls `.02745` because one replicate fails to
act consistently.

Five high-routine lives reproduce a positive result on both panels against
their newly generated same-run OFF cells:

| life | repeated A report / disjoint | A minus same-run OFF |
|---|---:|---:|
| `R2_B_seed0` | `.52909 / .27310` | `+.04845 / +.02746` |
| `R2_B_seed1` | `.52909 / .27310` | `+.03481 / +.02465` |
| `R2_B_seed3` | `.53038 / .27359` | `+.03106 / +.02234` |
| `R3_B_seed500` | `.52909 / .27310` | `+.04017 / +.02865` |
| `R3_B_seed502` | `.52909 / .27310` | `+.03531 / +.03036` |

The important correction is semantic. These are not one byte-identical
six-pass routine. Their modal actions include:

- the four-pass prefix plus `-instcombine` (`R2` seeds 0/1);
- plus `-instcombine,-constprop` (`R3` seed 500);
- plus `-instcombine,-dce` (`R3` seed 502); and
- plus `-instcombine,-dce,-adce` (`R2` seed 3).

The low attractor is usually the bare four-pass prefix and scores about
`.48779 / .24948`. The high family uses an extended suffix and commonly scores
about `.52909 / .27310`. Three intermediate lives (`R3` seeds 504/505 and `R4`
seed 602) retain their own dominant routines but have more variable later
actions and intermediate scores. Therefore:

- supported: repeated flat-text sleep installs a narrow, strongly repeated,
  life-specific action prior that survives a fresh stochastic fit and new
  generation seeds;
- supported: some installed routine families are useful across these fixed
  programs;
- not supported: conditional choice among memories, connected knowledge,
  compression, novel strategy discovery, own-experience theory formation, or
  lifetime improvement;
- not supported: prevalence estimates from `5/23`, because the twelve reruns
  were an adaptive diagnostic subset rather than a prospectively sampled
  confirmation set.

## OFF noise: generation seed versus execution history

Each standalone job has two entries, but they are not same-seed repeats: a job
started at seed `s` uses `s` for replicate 0 and `s+1000` for replicate 1.
Across two identical A40 nodes, three job seeds, two replicate positions and
both panels, the terminal values are:

| panel | pooled mean | SD over 12 panels | full range | mean / max absolute difference at the same seed across nodes |
|---|---:|---:|---:|---:|
| report (8 programs) | `.48568` | `.00560` | `.02131` | `.00561 / .01010` |
| disjoint (12 programs) | `.24591` | `.01145` | `.03776` | `.00582 / .01367` |

The cleanest seed comparison uses the first replicate from a fresh backend on
both nodes. Cross-node mean scores for seeds `4242`, `6262`, and `7272` span
only `.00430` on the report panel (`.48943`, `.48542`, `.48972`) but `.02763`
on disjoint (`.24990`, `.25109`, `.22346`). The low disjoint result at seed
`7272` appears on both nodes, so it is real generation-seed sensitivity, not
just one bad runtime.

Execution history is separately visible. The probe code supplies a derived
seed for every episode and tick, and all **120/120** first-turn prompts match
byte-for-byte across nodes. Nevertheless, only **84/120** first-turn outputs
match. Fresh replicate 0 matches `60/60`; replicate 1, generated after the
first panel has already run through the same backend, matches only `24/60`.
The exact cause is not isolated here (backend RNG/history and node execution
remain bundled), but explicit per-request seeds clearly do not reset all state.
Later prompts also contain real elapsed seconds in the `CLOCK`, so once an
execution diverges, its later prompts need not remain identical.

Consequences for later evidence:

1. Pool OFF over multiple independently started generation seeds; do not use a
   single within-life OFF realization as a precise ruler for `.01` effects.
2. Do not call two sequential reps in one backend exact common-random pairs.
   Paper-grade pairing needs a fresh backend per replicate and a deterministic
   clock/state rendering, or deterministic decoding/candidate scoring.
3. Retire the claim that disjoint is necessarily less noisy. In this sweep it
   is about twice as variable as report and contains a reproducible seed
   outlier.
4. The high legacy routine's roughly `+.043` report and `+.027` disjoint lift
   versus the pooled OFF means remains clearly visible as a routine-positive
   control. Smaller `.01--.02` effects do not clear this noise audit.

## Evidence locations and custody note

- Original A cells: `~/v6_out/pretest_write_ab/<life>/probes/` on nodes 1/2.
- A reruns: `~/v6_out/pretest_write_ab_Arep/<life>/probes/` on nodes 1/2.
- Standalone noise: `~/v6_out/off_noise/` on nodes 1/2.
- Probe/source hashes matched across nodes: `probe_adapter.py`
  `ddb7f90e...41b4f`, `batch_loop.py` `35156f13...a41`, `model_backend.py`
  `43602db0...6367f`, and disjoint panel
  `24ecfe87...003a`.

The node-1 ledgers were created after the previously recorded node-1 mirror.
They should be copied by the mutation owner before the node-1 lease ends; this
audit did not mutate or archive remote state.
