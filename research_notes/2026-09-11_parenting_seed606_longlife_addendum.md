# Parenting dynamics: seed-606 long-life addendum

Date: 2026-09-11

Status: **exploratory descriptive evidence only.** This is a fresh read-only
audit of one qualifying node-1 parenting life. It does not supersede the
five-life combined snapshot, estimate a causal parent effect, or qualify a
writer.

## Receipt and event

The source report is
`/private/tmp/parenting_dynamics_20260911_1239.json`, SHA-256
`6445616d8fd135b8b494bf0784700fc60523fb78c53b4ad511cdda912e0d970b`.
It found three R4 directories but only one internally analyzable event:
`R4_B_seed606`. Seeds 604 and 605 were excluded because their reconstructed
episode counts were eight beyond their nominal wake-receipt exposures (888 vs
880 and 760 vs 752). All three R3 controls were analyzable. The report
correctly sets `s4_sufficient=false`.

Seed 606 first received a valid v3 brief at episode 224. The 14B parent brief
had 74 lesson tokens, zero leak hits, exact text/metadata agreement, and
SHA-256
`c37a67778a75fd4a8c7474e3bfcfdd3586c211c0717bdffa886e819f868135a9`.

## Immediate and delayed observations

Each cell below summarizes 32 episode instances. “Different action” requires
change-intent language followed by a different, predicted, authoritative
executed action; generated ACT-like prose is never counted as execution.

| Window | Exact indexed brief visible | First-note overlap >=4 tokens | Broad change thought | Different predicted/executed action | Modal first action | Mean score |
|---|---:|---:|---:|---:|---:|---:|
| Pre, 192--223 | 0/32 | 4/32 | 0/32 | 0/32 | 31/32 | 0.5626 |
| Direct, 224--255 | 32/32 | 16/32 | 3/32 | 2/32 | 31/32 | 0.5673 |
| After one sleep, 256--287 | 32/32 | 23/32 | 5/32 | 3/32 | 26/32 | 0.5693 |
| Four-sleep window, 352--383 | 0/32 | 16/32 | 2/32 | 1/32 | 27/32 | 0.5675 |

The indexed brief was delivered for 96 episodes, apparently 224--319. The
four-sleep window is not a clean withdrawal window: another distinct valid
brief was first delivered there with substantially similar process content.

The strongest observation is lexical accommodation while the exact brief is
visible. The mean-score changes versus the pre-window are only +0.47, +0.67,
and +0.49 percentage points. Prediction error worsened from 0.0807 before the
brief to 0.1012 directly after it, 0.0895 after one sleep, and 0.0951 after
four. The first-action distribution did not change directly: it remained
31/32 modal with only two unique first actions.

A semantic check further weakens the automatic direct change-thought/action
counts. One cell at most weakly connected advice-like language to a changed
executed action; another was a negation false positive (“should not change”),
and a third mentioned a new approach without executing a different predicted
action. The analyzer does not directly score the brief's unique prescriptions:
ground a prediction in an observable feature, contrast a prior case, issue a
specific recall query, make one deliberate deviation, and name the belief
changed.

## What the adapter did, and why it is not a parenting result

All 15 parent-absent ON/OFF checkpoint pairs through episode 960 qualify.
Each repeats the same eight report programs, so there are 15 dependent panel
pairs, not 120 independent situations.

- Before the first parent brief, ON exceeded OFF at episodes 64, 128, and 192
  by +1.02, +0.96, and +5.39 percentage points.
- After the first brief, ON exceeded OFF at all 12 checkpoints by +0.16 to
  +6.05 points.
- Across all 15 checkpoints, ON had higher mean score, lower prediction SD,
  and higher adjacent-note similarity; it had lower
  non-improvement switching at 14/15 checkpoints.
- Yet the coarse advice-like action signature was suppressed by ON even
  before parenting. Before the brief, realized-change cells were 0/24 ON
  versus 9/24 OFF; afterward they were 1/96 ON versus 35/96 OFF.

The ON/OFF probes show that the realized adapter causally changes behavior on
this repeated panel under common-random generation seeds. They do not show
that parenting caused the adapter effect. In the archived per-program cells
through episode 640, much of the positive mean repeatedly came from the same
two programs, and the historical writer selected adapters using this report
panel. Ordinary self-learning, selection, parent-conditioned child
paraphrases, and continued intervention remain inseparable.

## Bounded conclusion

The supported statement is:

> In seed 606, a valid repeated parent brief entered every prompt in the
> immediate and one-sleep windows while the child's measured wording shifted.
> No constituent-level implementation of the lesson or durable task benefit
> was demonstrated. The LoRA changed behavior strongly, but that effect was
> already present before parenting and often opposed the coarse
> advice-associated action signature.

The highest-information next parenting scout is a short randomized
authentic-parent versus content-neutral-sham canary from one clean checkpoint.
It should teach one conditional process distinction, remove all parent and
lesson context, perform one matched write per fork, then evaluate changed
cases with authoritative actions and world outcomes. The primary estimator is
`(authentic ON - authentic OFF) - (sham ON - sham OFF)`. This is ordinary
scout work under the simple hygiene ruling; it is not C11.
