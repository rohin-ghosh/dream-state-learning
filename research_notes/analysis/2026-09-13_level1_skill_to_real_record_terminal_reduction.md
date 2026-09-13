# Terminal reduction: authored Level-1 skills versus real child-record formation

**Evidence cut:** 2026-09-13 08:37 UTC. This reduction was performed after the
result-blind audit in
`2026-09-13_level1_second_roster_result_blind_claim_audit.md`. I did not alter
any source, fit, root, score, job, or GPU state. Every cited root was terminal
and had a separate collected artifact before inspection.

## Verdict

The rank-8 writer can install all four tested **authored, explicitly prompted
Level-1 policies** at this dose. With one literal motor-syntax example in the
wake prompt, the real child action -> world outcome -> record path also becomes
executable. One of three perception fits then produces a large record-quality
gain over OFF (14/16 versus 7/16), while the other two produce only 8/16.
Therefore the bridge exists at this scale but is optimizer-sensitive and not
yet a stable learned child skill.

That distinction is unusually sharp:

- the authored policy screens move from weak OFF behavior to 47--48/48 after
  fitting, in every optimizer seed;
- the first interactive formation probe produces 0/16 executable actions and
  therefore 0/16 child-authored records for OFF and for all three fitted
  perception adapters;
- a prospectively frozen prompt amendment leaves the parser unchanged but adds
  one literal `ACT: TRY` syntax example. All four states then execute 16/16
  actions and author 16/16 records. OFF admits 7/16 records; perception seeds
  0/1/2 admit 14/16, 8/16, and 8/16.

This is not evidence that the four cognitive skills or real record formation
are impossible. The fixed sample shows a direct **dialect boundary**: the
interactive harness required `ACT: TRY a,b,c`, while otherwise plausible model
outputs emitted `TRY a,b,c` without `ACT:`. One fitted seed instead expanded
into prose and hit the token limit. The narrow Level-1 targets were JSON policy
answers, not native consciousness-loop continuations. The first break was
therefore between a skill demonstrated in its exam dialect and the same skill
being expressed through the child's motor interface. The prompt amendment
repairs that external syntax boundary and exposes the next, more informative
question: whether the adapter reliably carries prediction and relation binding
into self-authored records. Its answer is “one strong optimizer seed, two
nearly flat seeds.”

## Audited Level-1 roster

All cells use one material seed and three optimizer seeds. Each fit starts from
the same frozen Qwen2.5-7B-Instruct base and trains a fresh rank-8 LoRA on 96
authored rows for 320 updates / 1,280 row presentations. Each readout has 48
fresh held situations and 12 copy/add canaries. Counts below are exact
`content_correct`; strict format is identical to content for every post-fit
held output.

| Authored proxy | OFF held | Post held, seeds 0/1/2 | OFF canary | Post canary, seeds 0/1/2 |
|---|---:|---:|---:|---:|
| Perception | 21/48 | 47, 48, 48 /48 | 12/12 | 12, 12, 12 /12 |
| Self-reflection | 0/48 | 48, 48, 48 /48 | 12/12 | 12, 12, 12 /12 |
| Repetition | 0/48 | 48, 48, 48 /48 | 12/12 | 11, 11, 12 /12 |
| Meta-reflection | 9/48 | 48, 48, 48 /48 | 12/12 | 12, 12, 11 /12 |

The signs and near-ceiling endpoints are stable across optimizer seeds, but the
three seeds reuse the same authored material. They are not three curricula.
Perception and self-reflection use new held wrappers; repetition and
meta-reflection reuse the training wrapper families. Repetition and
meta-reflection each lose one canary in two of three seeds, so only perception
and self-reflection are canary-preserving under the audit's strict rule.

The strongest permitted statement is that a fresh LoRA fit improved execution
of an explicitly stated authored decision procedure on fresh authored
situations. These screens do not demonstrate actual perception, rehearsal,
self-reflection, SLEEP, parenting, or organism learning. The prompts state the
policies, and post-fit exact formatting is part of what was learned.

### Custody

Authoritative `scores.json` SHA-256 values, seeds 0/1/2:

- perception: `23d7cd4a...45687f`, `aac2327e...47a542`,
  `114529b5...0b286c`;
- self-reflection: `6db2ea03...8b834`, `f4bb78ad...aad4f`,
  `e2aa101d...f339`;
- repetition: `40d2b5df...def7`, `c03cdf18...dcdd`,
  `67703f3b...02b`;
- meta-reflection: `15b4a287...e5d3e`, `298c940b...2081`,
  `e4293175...f806`.

Full paths are under node 1 or node 2
`/localhome/local-rohing/astra_diagnostics/level1_<skill>_seed<seed>_20260913_attempt{1,2}_collected/scores.json`.

## Real-record formation probe

The follow-on probe used eight fresh mystery-box episodes and two scheduled
wake attempts per episode. It compared the frozen base with all three fitted
perception adapters. The world was allowed to execute only a single valid,
anchored `ACT: TRY` action. A record could be authored only after such an
execution.

| State | Wake calls | executable world actions | production-eligible records |
|---|---:|---:|---:|
| OFF | 16 | 0 | 0 |
| perception seed 0 | 16 | 0 | 0 |
| perception seed 1 | 16 | 0 | 0 |
| perception seed 2 | 16 | 0 | 0 |

The report has SHA-256
`2b9bb4d5539d6e26e75933af8d45e21e1dc3c93ad7320fc2bc6c64d1cf93420a`
at node 2
`/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt1_collected/formation_report.json`.
It is formation-only: no fit, write, quiz, downstream readout, or learning
claim.

In the first frozen sample, OFF emitted:

```text
PREDICT: T
TRY 5, 10, 15
```

Perception seeds 0 and 1 emitted the same unanchored shape with different
values. Seed 2 generated explanatory prose until `finish_reason=length`. Thus
the zero is real under the strict motor contract, but it is not a semantic
score of whether the proposed integer triple was useful. It localizes the
failure before world experience or record writing exists.

### Prompt-amended attempt 2

Before inspecting any attempt-2 outcome, the builder froze a format amendment
that changed only the wake instruction: it ended with a terminal two-line
contract, made the literal `ACT:` prefix explicit, and included one arbitrary
syntax example. It retained the original eight DEV episode IDs, all four
states, the strict action parser, record prompt/scorer, source joins, and call
budgets. Because it reuses the inspected DEV episodes and bundles more than
one wording change, this is an exploratory availability diagnostic, not fresh
confirmation or a pure causal estimate of the `ACT:` prefix.

| State | actions executed | record calls | admitted records | strict canonical records |
|---|---:|---:|---:|---:|
| OFF | 16/16 | 16/16 | 7/16 | 0/16 |
| perception seed 0 | 16/16 | 16/16 | 14/16 | 6/16 |
| perception seed 1 | 16/16 | 16/16 | 8/16 | 0/16 |
| perception seed 2 | 16/16 | 16/16 | 8/16 | 0/16 |

The exact report has SHA-256
`9d04155a0103377e41f80ad25b7b1b4ed9cd2ffd014503e74b27a0992b4c81f1`
at node 2
`/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt2_collected/formation_report.json`.

Every state copied the observed outcome correctly in 16/16 records. OFF got
the prior prediction field correct in 13/16 but the derived
matched/mismatched relation in only 7/16. Perception seed 0 got prediction and
relation correct in 14/16; seeds 1 and 2 got the relation correct in 8/16 and
11/16, respectively, but seed 2 also dropped or replaced the action field in
five records, leaving only 8 production-eligible records. Thus seed 0's gain
is substantive typed binding, not only JSON formatting. The disagreement
between three fits that were essentially indistinguishable on the authored
48-item perception exam is the important result: the easy exam does not
predict interactive record formation reliably.

## Consequence for the next experiment

Do not spend another roster merely proving that an authored JSON procedure can
be fit. Do not merely repeat the syntax scaffold either: it has already shown
that the world/record path can run. The next bridge must preserve the strict
interface while putting the skill into the same native sequence in which the
child must use it:

1. child emits canonical `PREDICT:` and exactly one `ACT:`;
2. the world executes the action and returns the outcome;
3. child emits a typed, evidence-bound `EVENT` or `NOTE` in its own words;
4. only that child-authored continuation is eligible for compilation;
5. after SLEEP, a fresh cue tests whether the bound event or relation is
   available without the episode transcript.

This is substantially closer to the already-audited PCFL vertical DEV v2 than
to another authored Level-1 screen. If a smaller precursor is used, it should
compare native-dialect skill targets against the current JSON skill targets on
fresh episode IDs and a new material seed, with strict action validity and
source-faithful record formation as the endpoints. It must not loosen the
parser to turn `TRY` into `ACT: TRY`, because that would hide the interface
failure rather than teach the child to operate its motor channel. Most
importantly, the selection gate must be the interactive record endpoint, not
the now-ceiling authored exam.

The separate keyed-discrimination v2 diagnostic is also now independently
audit-passed. It cleanly tests whether a truthful contrast instruction improves
answer-hidden keyed carriage, but it remains an authored acquisition assay and
does not substitute for this interactive bridge.
