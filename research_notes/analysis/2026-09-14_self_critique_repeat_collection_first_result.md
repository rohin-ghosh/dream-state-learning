# Critique versus repeat — first terminal result, 2026-09-14

**Bounded collection COMPLETE; zero fit candidates; ownership released.**
Both arms retain all16 fixed TRAIN tasks/eight opposite-goal pairs. Critique
gets6/16 goals versus repeat4/16, but both get1/8 pairs. Neither supplies a
complete four-read/two-route/six-target episode. No fit, semantic approval,
learned-self-reflection, grounded-memory-use or generalization claim follows.
This is the author's frozen-source artifact reduction; independent review is
separate, not claimed by this memo.

## Source, intervention and publication

Exact executed source `3b1b07c324d4841fbba48fe201069e3eaf9fc2b5` was pushed
before staging. Protocol
`2026-09-14_self_critique_repeat_collection_protocol.md` SHA256
`154b7642113e48068e7357efb6a1d4c956dc151e030472fcb3f6ac98e696883a`.
The actor explicitly uses Schrodinger's V3 `allow_colon_header=True`, plus
the strict plain-command parser; original V1/V2 defaults remain unchanged.
No command repair, teacher source plan, PROBE model input or score is supplied.

Reuse original rich shard0's four TRAIN source worlds in fixed order. All16
intervention pairs have byte-identical initial public histories, task/source
IDs and system text; only the critique-versus-repeat-planning instruction
differs. Both receive ordinary public outcomes: this is NOT feedback versus
blindness. Each raw child intervention is fallible advice, not authoritative
evidence. All initial failures remain in both arms; no success selection.

Prelaunch receipt commit `4e5841fcc4e474af4ed171e8dc9a1138333d2eba` was
successfully pushed and verified ancestral to fetched origin/main before
launch. Both actual no-model prepares passed. Every new launch path used
`set -euo pipefail`; no failed prelaunch publication was ignored.
A later status push of `11bf3eb0` was rejected after both arms were running;
the shell stopped, no force-push/extra launch occurred, and Main subsequently
merged the concurrent notebook history. This does not alter or backdate the
successful prelaunch gate. Nash's separate logging-order deviation is not
part of this branch and is not erased.

## Recomputed counts and preserved failures

| Endpoint | Shared initial | SELF_CRITIQUE_REVISE | REPEAT_NO_FEEDBACK |
|---|---:|---:|---:|
| Goals | 4/16 | 6/16 | 4/16 |
| Strict opposite-goal pairs | 0/8 | 1/8 | 1/8 |
| Outcome-eligible six-turn episodes | 0/16 | 0/16 | 0/16 |
| Candidate rows | 0 | 0 | 0 |
| Actor calls | 25 | 38 | 32 |
| Intervention calls | 0 | 16 | 16 |
| Total native calls | 25 | 54 | 48 |
| Actor callback-error stops | 9 | 8 | 8 |
| Dead ends | 3 | 0 | 4 |
| Invalid-route stops | 0 | 2 | 0 |
| All memory reads | 2 | 13 | 7 |
| Generated tokens, recorded | 2,048 | 7,518 | 5,474 |
| Prompt tokens, recorded | 7,560 | 32,771 | 25,897 |

All127 Engine-call errors are null, but that does not mean all outputs are
valid. Actor callback errors reduce to `not exact short ROUTE` (5/6/5) and
`single_action_delimiter_required` (4/2/3), respectively. No fixes were supplied.
One critique (TRAIN-C/task3) and one repeat plan (TRAIN-B/task0) are
`nonterminal_or_truncated`; their raw outputs remain captured and the declared
unavailable-advice marker was used. They are not invented successful critiques.
Recorded contexts are <=2,048 and generated lengths <=512. Counts are from
captured token metadata, not independent retokenization.

Both arms' sole successful pair is TRAIN-D/tasks(0,2), with the required two
legal commits and distinct source-correct first ports. All four initial goal
successes used zero READs. Critique's TRAIN-B/task2 success used three READs;
its other five successes used none. Repeat's TRAIN-D/task2 used one READ;
its other three successes used none. Thus the extra individual critique goals
do not establish reliable goal-directed use of retrieved memories. No success
has the four-read/six-target form required for this candidate collection.

The content floor is unchanged: outcome AND useful grounded articulation,
with unresolved judgments excluded. Zero episodes reach the outcome floor,
so no episode is content-approved and no critic text silently becomes a fit
target. The32 intervention captures remain a separate, unreviewed pool,
including both nonterminal failures. There is no automatic semantic pass.

## Costs, states and finite closure

Guardians143969/143970 started19:58:07UTC on reserved A100GPU4/5. Shared
initial native143996 ran19:58:08.403–20:00:59.708UTC (171.304576s).
Critique native144358 ran20:01:12.400–20:08:22.308UTC (429.908133s);
repeat native144367 ran20:01:15.575–20:06:52.268UTC (336.693284s).
Both guards exited0, at20:08:23 and20:06:53UTC. All owned guardian/timeout/
native PIDs are absent; terminal GPU4/5 observations show0MiB/0percent.
No other processes were stopped and no other GPUs were used.

Total native-phase wall time937.905992s (~0.260529 allocated A100-hours);
guard intervals total1,142s (~0.317222 hours), including the repeat wait for
the shared initial phase. CPU source preparation/transfer is separate.
Both stayed below their admission/teardown-inclusive two-hour ceilings.
Shared initial cost is reported separately, not attributed twice to inference.
Equal112-call/512-token arm ceilings did not yield equal spent calls, tokens,
or compute. This is not an equal-spent-budget efficiency result.

All three phases join recorded before/after state
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`,
unchanged-base flags, read-only adapter use and zero fits/updates. File/hash
checks and frozen replay are not independent authentication of live tensors.
Same exposed DEV learner, four fixed TRAIN instances, one deterministic
comparison, no held/environment-transfer test and no persistent parameter
change: the pair tie and empty candidate set do not support learned reflection
or H1/H2, nor prove critique can never help. This finite recipe is closed.

## Evidence and author checks

Native root: `/tmp/astra_self_critique_repeat_20260914_attempt1` on A100.
Local capsule:
`gpu_artifacts_local/astra_self_critique_repeat_terminal_20260914_attempt1/extracted`.
Sibling `terminal.tar.gz` SHA256:
`23ddf8f02f802b5244d26657ca9f35f8f466ae9151f8654dffff0287fe9ccd76`.
Source archive SHA256:
`2541554fa2cdbd31aef7216210e76deea1106081748ad3c70f7c330a9e522188`.
Shared initial RESULT SHA256:
`6ce60c01e4a7400c55d4f2153cdd2f34b64f7c81f0c1b68cb0e29c5ac8becef8`.
`CPU_REDUCTION.json` beside the extracted directory SHA256:
`6576c2056d21cdc2595bc4ab9680c7248ecfb38f3e0177cddb800a21bb4686f6`.

Fresh source gate:22 CPU unittests passed, including17 owned tests and the five
shared V3 tests; actual original40-call EXPOSE replay and four-TRAIN selection
passed. Post-run checks: safe unique6,356-entry archive inventory; seven
bounded source files match Git objects; all127 native captures join frozen
replay, projections, summaries, role counts, token metadata, exact stage-file
inventories, initial/source bindings and recorded state files. Both arms'
16 intervention histories match exactly before their instruction suffixes.
No model/tokenizer imports or network operations were used for reduction.
An initial review-script guard incorrectly blocked the standard library's
`socket` import through `email`; it was replaced with a socket-operation audit
guard and the reduction passed. This was a review-script error, not a native
failure. Raw native evidence and frozen source were not changed.

**GPU4/5 and implementation/result ownership released to Main.** No further
native calls, repairs, fits, paper edits or broad ancestry review are queued.
