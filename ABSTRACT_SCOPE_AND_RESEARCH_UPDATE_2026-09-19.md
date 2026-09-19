# Research update and recommended abstract scope

**Date:** September 19, 2026 (Pacific time)

**Status:** Discussion summary and scope recommendation, not a ratified change
to the project's thesis, benchmark, or experimental invariants. Operational
statements describe the latest receipts reviewed for this update; saving this
document is not a new live-fleet audit.

## Bottom line

We have real findings and a promising early result, but not yet a clean
demonstration of an agent that reliably gets better through continued
experience. Keep that ambition while making this submission much narrower.

The early C2 result gives us a reason to pursue this. The later decline and
correction failures tell us what the paper must explain. The strongest scope
is not to abandon the big idea, but to prove one essential piece properly.

## Submission deadlines

The ICLR 2027 Call for Papers and Author Guidelines were checked for this
update:

- **Abstract:** September 19, 2026, at **4:59 a.m. PDT**
  (September 18, 11:59 p.m. Anywhere on Earth).
- **Paper:** September 26, 2026, at **4:59 a.m. PDT**
  (September 25, 11:59 p.m. Anywhere on Earth).
- Titles and abstracts can be refined before the paper deadline, but the
  abstract submitted now must be substantive, not a placeholder.
- The author list locks at the abstract deadline; author order can still be
  changed before the paper deadline.

Submit an honest scope now rather than waiting for the experiments to resolve.

## What the evidence supports

### 1. Controlled results for the underlying learning mechanism

Earlier experiments show that adapters can acquire taught behavior and facts,
that competing updates can erase unrehearsed behavior, and that rehearsal and
mixed batches preserve learning.

For example, the unrehearsed habit fell to **0/32 after 16 competing updates
across three optimizer seeds**, while the zero-learning-rate control retained
**32/32**.

These are narrow mechanism results, not the full developmental-agent claim.

**Receipt:** `research_notes/SUCCESSES_AND_LAWS_2026-09-14.md:5`

### 2. A promising early C2 exploration result, followed by decline

At the same **3,072 generated tokens per evaluation seed**, the reconciled
caption results are:

| Checkpoint | New pixels, seed 23201 | New pixels, seed 23202 |
| --- | ---: | ---: |
| Frozen base | 15 | 24 |
| C2 sleep51 | **34** | **31** |
| C2 sleep117 | 19 | 26 |

The counting dispute is resolved: replayed responses inflated the alternative
totals. The table reports the deduplicated, same-block numbers.

Important limitations:

- "Pixels" measure the game's operational novelty, not independently verified
  funny ideas or globally unique ideas.
- Two sampling seeds from one lineage are not replicated training runs.
- These are pinned historical checkpoints, not a measurement of current live
  C2 weights.
- The result does not establish a causal advantage from consolidation or broad
  superiority over the base model.

**Interpretation:** Something worth investigating happened by sleep51, but more
development did not reliably improve it. The rise-and-decline pattern is more
defensible than a claim that the system keeps getting smarter.

**Receipt:**
`research_loop/workers/post_recovery_c2_age_eval_20260918/RESULTS.md:7`

### 3. The missing link: turning corrections into behavior

The bounded correction review found no complete chain of:

> Recognize feedback → fix the next action → repeat the correction without a
> reminder.

Some corrections disappeared during compaction. Others were visibly present
and still produced promises instead of artifacts. Not every failure can be
explained by infrastructure.

This is a finding about the sampled correction chains, not a claim that no
life has ever corrected itself.

**Receipt:**
`research_loop/workers/post_recovery_correction_review_20260919_0139/REVIEW.md:8`

## Execution and repository status

The useful code and receipts were pushed. The verified remote `main` commit
for this update is:

```text
0227ba4c3f1f0fae7e17f88b5b2a80122fccc85f
```

The latest work restored one caption player's parent delivery and completed a
frozen-sibling probe. That is progress, but not evidence that the fleet is
healthy end to end:

- The caption player's scoring remains blocked by oversized journal transport.
- C0/Astra7 recovery remains tested but uninstalled.
- The retention fix is not established as deployed.

These are unfinished implementation jobs, not scientific negative results.

**Receipt:**
`research_notes/analysis/CONTINUATION_RECEIPTS_2026-09-19.md:75`

## Recommended paper scope

### Central question

> When does parent-guided experience become retained behavior in a language
> agent?

This preserves the project's thesis. It makes **retention and transfer the
primary target**, with faster autonomous learning—the stronger H2 claim—as the
next step rather than an assumed result.

### Working title

**From Feedback to Retained Behavior: Studying Parent-Guided Language Agents**

### What the abstract can honestly cover

- Consolidation of experience into adapters.
- Interference and the role of rehearsal.
- The gap between feedback delivery and correction uptake.
- Checkpoint-dependent exploration under fixed token budgets.
- Controls that distinguish context scaffolding from parameter learning.

The abstract should not yet claim general self-improvement. This is a proposed
scope, not a claim that all of the experiments below have already succeeded.

## Priorities for the remaining experimental time

### 1. Complete one controlled learning chain

Use checkable tasks. Verify that feedback actually reaches the action. Measure
the correction immediately, after sleep, and in a fresh parent-free context.

The essential sequence is:

> Actual feedback → visible correction → correct next action → unreminded
> reuse → post-sleep retention → fresh-context transfer.

### 2. Run strong controls across independent training seeds

Use at least three independent training seeds, not merely multiple sampling
seeds from the same trained lineage.

Compare learning against a frozen sibling with matched opportunities for
parenting. Add adapter-on/off fresh-context probes to separate learned behavior
from context scaffolding.

### 3. Repeat fixed-token developmental probes

Test early and later checkpoints on fresh problems. Measure whether capability
improves, rather than whether lifetime accumulated discoveries increase.

### 4. Keep captions secondary until validated

Keep the exploration curves, but independently audit accepted captions and
separate transport failures from unsuccessful guesses.

### 5. Attempt the stronger H2 comparison if time permits

If the preceding experiments succeed early enough, run the
**parented/unparented × continued-sleep/frozen** comparison needed for H2.
Otherwise, report H2 as unresolved.

## Research judgment

Do not spend the remaining days expanding the fleet or adding more curricula.
One replicated causal result is worth more now than another hundred hours of
complicated trajectories.

The strongest submission would connect the controlled mechanism findings to
one demonstrated case of retained, transferable correction, while explaining
the observed failures and developmental decline honestly. It should keep the
larger self-learning thesis as the motivation, not present it as an established
outcome.
