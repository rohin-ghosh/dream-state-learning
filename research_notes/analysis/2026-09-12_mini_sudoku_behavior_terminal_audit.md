# Mini-Sudoku useful-versus-corrupt behavior: terminal independent audit

**Verdict: a strong directional material effect, but not a qualified behavior
positive control.** Correct prompt-solution pairings changed later first
actions substantially more than an equal-marginal cyclic wrong-board corpus.
The useful adapter produced two exact held-out solutions where OFF and corrupt
produced none. It nevertheless misses the independently specified strong gate,
uses one optimizer seed, and was executed before prompt-clock/token custody and
material-to-adapter receipts were closed. Treat this as evidence that material
semantics matter to behavior, not that the current writer is selective or
paper-ready.

## Terminal state and fixed scope

Attempt 3 completed both 96-step rank-8 fits and all 64 fresh-process probe
episodes under:

`/localhome/local-rohing/astra_diagnostics/`
`astra_mini_sudoku_useful_corrupt_20260912_attempt3`

Both arms used 32 training puzzles and the same target-grid text/token
multiset. `useful` paired each prompt with its independently validated native
solution; `corrupt` cyclically assigned a different training puzzle's solution.
Evaluation used 16 puzzle-disjoint canaries, one tick and one first action. This
is external-oracle material, not child-authored SLEEP, parenting, retention,
clean lineage, or H1/H2 evidence.

The useful and corrupt PAIR_DONE receipts finished at `10:41:49` and
`10:41:26` UTC. The two independently generated OFF result files have the
identical SHA-256 `34954d1f...2fba2`, so the base behavior reproduced exactly
across GPUs 1 and 3. Useful and corrupt ON result SHA-256s are respectively
`94e8c61b...e9eb7` and `6e42255f...ed04`.

## First-action result

All scores below zero-fill missing or unusable first actions. Because the run
had one tick and one attempted action per episode, no later-action rescue is
possible.

| condition | nonempty recorded best action | exact solves | mean native partial score | strict valid Sudoku | givens-consistent board |
|---|---:|---:|---:|---:|---:|
| common OFF | 4/16 | 0/16 | `0.1125` | 0/16 | 1/16 |
| useful ON | 16/16 | 2/16 | `0.58555` | 2/16 | 4/16 |
| corrupt ON | 16/16 | 0/16 | `0.28828` | 0/16 | 0/16 |

Contrasts:

- useful minus OFF mean score: `+0.47305`;
- corrupt minus OFF mean score: `+0.17578`;
- useful minus corrupt mean score: `+0.29727`;
- useful beat corrupt on 13/16 boards, tied on 1, and lost on 2;
- exact-solve difference useful minus both comparators: `+2/16`.

The two exact useful solves were `rg/mini_sudoku/1900060` and `1900062`.
Neither is among the four disclosed evaluation IDs whose completed solution
grid also occurs in training (`1900054`, `1900055`, `1900059`, `1900065`).

The adapters completed the same 96 steps and 77,124 input-token passes. Final
training loss was `0.0363` for useful and `0.2088` for corrupt. That loss gap is
consistent with correct prompt-answer pairs aligning better with the base
model, but training loss is not itself a behavior endpoint.

## What the result means

Both adapters moved marker/full-grid production from 4/16 to 16/16. That shared
change is format learning. The corrupt adapter's partial-score improvement is
also unsurprising: it saw well-formed Sudoku grids even though each was bound
to the wrong puzzle. The additional useful-over-corrupt improvement, the 13/16
paired sign, and the two non-overlap exact solves are the evidence that correct
semantic pairing affected later actions beyond format alone.

This is exactly the narrow fact the diagnostic was intended to expose: the
writer is not indifferent to useful versus corrupted material. It does **not**
show strong enough extraction for the architecture's downstream claim. The
result-blind independent audit specified a strong gate before this watcher
inspected the probe results: useful >=12/16 exact, >=8 solves over both
comparators, and >=.40 mean-score gains over both. Actual useful was 2/16 exact
and +.297 over corrupt, so it fails that strong gate.

## Remaining limitations and next action

Attempt 3 started before the exact-byte independent audit completed. It lacks:

- a deterministic shared CLOCK and actual HF/vLLM prompt-token equality
  receipt;
- independent unique-solution enumeration for all 48 puzzles;
- a material -> trainer manifest -> adapter -> probe custody join;
- same-GPU sequential fits or crossed-device training; and
- independent optimizer-seed replication.

Exact OFF reproduction makes a large inference-hardware explanation unlikely,
but does not remove the useful-versus-corrupt training-device confound. These
limitations prevent certification; they do not erase the observed direction.

Do not enlarge this diagnostic yet. The highest-value implication is to keep
the semantic contrast in W0/SLEEP material and stop treating lower LR alone as
the writer fix. If a behavior-positive-control claim becomes necessary, repair
the custody seams and rerun optimizer seeds 1 and 2 prospectively. Otherwise,
move GPU effort to semantic W0, which directly tests conditional native action
binding and is the gate for authentic action-outcome SLEEP.
