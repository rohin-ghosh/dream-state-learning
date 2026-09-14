# Conditional three-view rich fit: smallest prospective pilot

**WITHDRAWN 2026-09-14: Main rejects the 12-row corpus for inadequate
coverage (two worlds, no opposite-goal pair); content review also excludes
both episodes. Do not implement or fit this historical proposal. V3 is a
separate prospective parser-compatibility collection, not its approval.**

2026-09-14. **DESIGN ONLY. Requires completed shared content review, Main's
selection, and a bound implementation/CPU admission before any fit.**
No automatic training follows collection or this proposal.

## Fixed source and minimum coverage

Use ONLY action-first terminal capsule SHA256
`508b12e464ee4379fce750675822235d4c23096ac6149ad6c39545dca1f672e7`,
from exact source60dbf789 and all four original rich shards. Its independent
primary is74calls,64attempted episodes,2action-complete episodes,12candidate
turns. This proposal knows those execution counts, not their content verdicts.
No world, episode, arm, or dose is selected using a fit/readout result.

Apply shared content contract SHA256
`3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b` to
EVERY candidate turn. Resolve and preserve reviewer disagreements. Keep every
episode whose six turns PASS; any FAIL/UNRESOLVED excludes that entire episode
from ALL views. Sort common retained IDs by shard/world/task/episode-call order.
Bind original row/call/source hashes and review decisions in one immutable
admission manifest; do not rewrite the original unreviewed source objects.

**Pilot feasibility floor: N>=6, a whole qualified episode from at least one
TRAIN world; N is a multiple of six.** For this closed capsule N can only be
0,6,12. N=0 means NO FIT, not recollection, relaxed review, or another dose.
This minimal floor permits a row-form pilot if any genuine qualified data
exist; it is not evidence of representative goal/world coverage. Report attrition
from all64planned episodes/16TRAINworlds/4shards, not only the retained subset.
Even N=12 covers only two worlds/two shards, second-goal tasks2/3, and no complete
within-world opposite-goal pair. No breadth/acquisition-population claim follows.

## Three states, one data selection and schedule

All fits start independently from the SAME37ec adapter and frozen Qwen2.5-7B
base: rank8, seed0, fresh AdamW, LR3e-5, batch4. Reuse existing frozen optimizer
settings, LoRA-only/base/finite-gradient/update/save checks; no sweep or early
stopping by task score. Original222 saved rows and their exact encodings remain:
128memory,20cue,62audit,12actual old trajectories. Validate their existing
saved source/native-capture provenance, not a newly invented ancestor binding.

For the N common new rows:
- **TERSE:** actual exact action slice + EOT; public prefix masked.
- **RICH:** actual full child response + EOT; public prefix masked.
- **RICH_ACTION_ONLY:** identical full input IDs to RICH, but rationale/delimiter
  labels masked; only actual action + EOT supervised. It still receives the
  teacher-forced rationale as context; this is not a no-rationale-exposure arm.

Parent/coaching text is absent from every student prefix. All suffix LF labels
are masked. No rewritten target, model-generated replacement, or critic target.
Exact template/action-token boundaries and <=2048 encoded context must hold
for ALL views; preparation failure cannot silently drop a row or train one arm.

Let M=12+N and U=8*M. For update u=1..U, offset=u-1, use shared global row order
old222 followed by N new rows, and indexes:

```text
(offset % 128,
 128 + offset % 82,
 210 + (2*offset) % M,
 210 + (2*offset+1) % M)
```

Thus every old/new trajectory target receives exactly16presentations; each
legacy slot contributes U presentations, not16 per legacy record. N=6 gives
144updates; N=12 gives192. Freeze the chosen schedule once after review.

Use **common RICH-reference causal-label normalization**, including identical
legacy labels. At each update let D count active labels after causal shifting
in the full-RICH reference batch. Each arm's loss is its summed active-token
cross entropy divided by that SAME D. With a native active-token mean this is
`mean_loss * active_causal_labels / reference_causal_labels`. Do not use an
arm-specific denominator or mean of row losses. Log every batch's reference
and actual active counts and aggregate tokens. RICH/TERSE differ in input length;
matched updates/reference normalization is NOT equal-token or equal-compute.

## One fresh, teacher-free readout for all four states

Evaluate a fresh37ec parent reference and each saved new adapter with identical
frozen source, worlds, memory service and public prompts. Use the exact
`ACTION_FIRST_PROTOCOL['public_system']` from60db; no articulation/parent append,
source plan or private answer in the user message. A response may be one strict
bare command or the exact RATIONALE/ACTION envelope; preserve native raw and
execute only its exact action projection. Ambiguous/nonterminal/malformed output
remains failure. Never strip `RATIONALE:` or substitute a planned command.
Content findings do not block a valid action. Fresh-process state/base checks
apply to every panel. Do not reuse the command-only v1 baseline as prompt-matched.

Fixed panel per state, <=384native calls:
- All four PROBE worlds, all4tasks each, OWN_TEXT and UNAVAILABLE: <=192calls.
  Primary: OWN_TEXT individual goals/16 and strict opposite-goal pairs/8,
  with each world's counts. UNAVAILABLE is the declared external service, not
  a parametric-memory failure claim; no fallback or hidden record access.
- Exactly TRAIN-A from each shard, all4tasks OWN_TEXT: <=96calls. This choice
  is fixed, not swapped to include a surviving candidate world. Report fit overlap;
  these are TRAIN-split diagnostics, not a census of newly fitted worlds.
- Old retention panel <=96calls:16old memories W0/W8 (32),16held audit cases,
  original taught graph OWN_TEXT (<=24), previous fresh graph OWN_TEXT (<=24).
  Use the same public actor interface for both graph panels across all states;
  keep memory/audit tasks unchanged. Re-evaluate37ec here too, not reused scores.

Graph actor cap512tokens/2048context for all states; memory/audit cap160 as before.
All inputs to OWN_TEXT remain actual captured child records. Report all raw
actions, invalids, reads/commits, individual/pair results and retention counts.
Separately grade natural content under the shared stage floor, blind to state
label where practicable. Report all attempted PROBE episodes, content
PASS/FAIL/UNRESOLVED and action-complete-with-all-turns-PASS rates; do not report
richness only among successful episodes. Bare commands can pass execution but
cannot satisfy the explanation floor. No heading/length-based quality score.

Primary contrasts: RICH minus TERSE and RICH minus RICH_ACTION_ONLY on the SAME
eight held pairs, with individual/world counts, fresh parent and retention.
Report all contrasts even if negative. Three seed0 fits/four probe worlds are
an exploratory mechanistic comparison, not independent population replication.

## Bounded execution and pre-GPU tests

After admission/Main selection: A100GPU3 can run the fresh parent readout while
GPUs0–2 run the three fixed fits; baseline scores never gate fitting. Each arm's
saved adapter then gets its own fresh readout process. Preserve failures and
never refit after a readout error. Reuse existing physical/CVD and six-hour lease
checks; no new guard framework. Proposed ceilings: parent3960s; each fit+readout
7680s (300admission, two3600s stages/two60s teardowns,60final reserve), maximum
7.5allocated A100-hours. Main must bind these ceilings with the selected recipe.

CPU tests must cover: N0 fail-closed and N6/N12 schedules; exact16 trajectory
presentations; common reviewed IDs/source hashes across views; causal-shift D
and differing active counts; legacy encodings unchanged; exact action-only
masks/EOT and context rejection; no parent text; fresh37ec/new-state joins;
384-call panel inventory and exact projection of both permitted response forms;
malformed/no-fallback failures; baseline-independent training and no-refit paths.
No fit/content promotion is authorized by passing these tests alone.
