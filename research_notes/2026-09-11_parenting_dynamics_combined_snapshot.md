# Parenting dynamics: combined two-node scout snapshot

Date: 2026-09-11

Status: **exploratory descriptive update only.** This combines read-only
outputs from the already-running R4 parented and R3 unparented histories on
the two A40 nodes. The histories were not randomized, the parent policy and
model differ across lives, and the historical writer selected writes on the
report panel. Nothing below estimates a causal parenting effect.

## Receipts and inclusion

The reviewed analyzer was run separately against each node's live receipt
tree:

- node 1 output SHA-256
  `cc1b4d9c07287cba120412f90ad7484a8539b8db0ea70feafae6fa93da285501`;
- node 2 output SHA-256
  `e9d6df273ca873cc7ac30464365bd2265df608c70b045b87e82a305ab2176ac5`;
- analyzer: `organism_v6/parenting_dynamics.py`, commit `aecf07df`.

The five raw indexed `parent_brief.txt` files were also inspected directly.
Their SHA-256 values for R4 seeds 600--604 are, respectively,
`a04122d10f816571aea7b77652a2eced4b4953f4cd1602f9fc444d44edf1d60a`,
`0808e9c0d878208b2fe3bbd571c6e94201054dd9ebcfd4e06372ab8a05f1b83c`,
`0f852059f4f30cb3321376a0e9f4223a3d1fb0800ca4e957275fc0b5eaef4232`,
`0ff41601c570a2560ba4222b5037292079eb329f0657e0369f68b2666cc474a8`,
and `2a53835a172943fdcc7260f88752d4eb5660e4911b7bc5d4b1eafedacb9a87a8`.

Five parented lives have an exactly delivered, valid v3 brief and enough
receipt-complete data for every 32-episode window: R4 seeds 600--604. Six R3
controls (500--505) have the corresponding threshold-aligned windows. R4
seeds 605 and 606 remain excluded because each ledger reconstructs eight more
episode instances than its committed wake exposure, consistent with a
resume/replay boundary. RP seeds 400--402 remain excluded by the earlier
lineage audit.

The first valid brief was delivered at episode 160--256. Four parent lives
used the 14B parent and one used the 32B parent. Three later life-windows
across two lives contain the first delivery of another valid brief; the
indexed brief has zero exact-delivery coverage in those windows. Thus even
this descriptive comparison is a mixture of teaching policies, parent models,
policy replacement, and continued intervention.

## What moved

Every number below is the mean within-life change from that life's 32 episodes
immediately before the event. Parent and control columns average one summary
per distinct life; independence is not established, and episodes are not
treated as independent replicates.

| Measure | Window | Parented (5 lives) | Controls (6 lives) |
|---|---|---:|---:|
| Thought mentions changing route | next 32 | +0.075 | -0.047 |
| | after one sleep | +0.019 | -0.094 |
| | after four sleeps | +0.069 | -0.120 |
| Episode has change-intent language and a later different predicted/executed action | next 32 | +0.019 | -0.010 |
| | after one sleep | +0.025 | -0.047 |
| | after four sleeps | +0.000 | -0.057 |
| Mean best task score | next 32 | -0.0004 | +0.0031 |
| | after one sleep | +0.0033 | +0.0050 |
| | after four sleeps | -0.0054 | +0.0083 |
| Mean executed attempts | next 32 | -6.96 | +2.17 |
| | after one sleep | -7.15 | -1.32 |
| | after four sleeps | -5.62 | -7.91 |

The parent-group mean remains above its own baseline for language about
reconsidering a route while the historical control-group mean declines. This
is heterogeneous: only two of five parent-life four-sleep deltas are positive
and drive the positive group mean. The coarse within-episode co-occurrence of
change language and a later different predicted/executed action is much
smaller and averages zero four sleeps later. No corresponding positive
four-sleep mean task-score delta was observed. The direct and one-sleep parent
windows also execute materially fewer attempts than their own pre-brief
windows; because assignment was not randomized, this is a warning to measure
rather than an attributed harm.

Lexical rehearsal is not summarized as learning. Several children already
produced first-note language overlapping the later indexed brief before
receiving it, and lesson-token rehearsal (at least four overlapping content
tokens in the first note) often remained high while the coarse action
co-occurrence vanished.

## What the parent actually prescribed

The five indexed briefs share two design features that motivate direct tests;
these are content-audit observations and hypothesized failure modes, not
explanations of the observed outcomes:

1. Every brief instructs the child to try one different or new action per
   episode. The action is not required to distinguish two live hypotheses or
   to follow from an observed failure. This prescribes novelty by schedule
   rather than requiring information-seeking exploration.
2. Every brief ends with the same mandatory first-note restatement. The
   policy therefore responds to one verbal ritual by prescribing another.
   High post-event token overlap is not evidence of spontaneous
   internalization: the prompt explicitly requests restatement, and overlap
   was already high before the indexed brief in several lives.

Several briefs also ground their examples in hypothetical program properties
such as being memory-heavy or containing more loops, without identifying
evidence in the child's record that those properties were observable. A
situation-specific rule cannot be evaluated unless its proposed cue is
actually available to the child.

These are hypothesized teaching-policy failure modes, not post-hoc exclusions.
All five lives remain in the descriptive table. A proposed next lesson is:
name two live
hypotheses, choose one cheap action whose possible outcomes separate them,
state the stopping/review condition, execute it, and later test the resulting
bounded lesson in a changed case.

## Bounded reading

The larger snapshot supports this deliberately descriptive conclusion:

> In these historical scouts, the parented-group mean retained more
> change-intent language after its indexed event than the threshold-triggered
> control-group mean, but this contrast was heterogeneous and descriptive. At
> four scheduled sleeps, the parented mean task-score delta was negative and
> the coarse within-episode change-language/action co-occurrence delta averaged
> zero.

Material confounds include threshold-triggered regression to the mean, event
age imbalance (parent events at 160--256 episodes; controls at 128--160), node
and group imbalance (parent lives split 1+4; controls 3+3), different parent
models and policies, and continued adaptive parenting rather than withdrawal
in later windows.

This makes the next teaching target concrete: after considering a different
route, the child must commit to one small discriminating action, observe its
outcome, and later choose differently in a changed case. Echo and advice
agreement remain diagnostics only. A clean parent-versus-sham canary still
requires matched schedules, fresh parent state per clean root, parent-absent
changed-case reads, and a writer that has independently passed specificity,
retention, interface, and non-harm checks.

The full C11 guard remains parked for the final paper-grade run.
