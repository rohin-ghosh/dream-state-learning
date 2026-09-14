# SEQ267: posthoc progress and feedback diagnostic

Old builder supplementary analysis, 2026-09-14. No campaign allocation,
new model calls, fit, admission change, or replacement of the primary result.
The closed Taxi screen remains RICH0/16 versus TERSE0/16 deliveries.

## Question and method

Where did the six-turn trajectories become unable to finish, even with an
optimal continuation? Replay all32 saved episodes/192 turns against the frozen
native transition bank. Reconstruct each observation and feedback history,
reproduce strict parsing, and measure shortest native delivery distance before
and after each action. A prefix is feasible if distance <= remaining turns.
Progress means reduced distance, not successful delivery or evidence of learning.

Source: `research_notes/analysis/orch_game_20260914_attempt1/` and its
`native_evidence/shard*/screen/*_EPISODE.json`. The companion JSON binds the
bank,32 episode files and analysis dependency by SHA256. This is a read-only
posthoc diagnostic; initial states and all original denominators remain fixed.

## Results

| Diagnostic | RICH | TERSE |
|---|---:|---:|
| First-turn distance reduction |3/16|1/16|
| First-turn distance increase |6/16|12/16|
| First-turn unchanged distance |0/16|3/16|
| First-turn format rejection |7/16|0/16|
| Turns beginning with feasible continuation |36/96|25/96|
| Distance reduction on feasible turns |10/36|2/25|
| Distance increase on feasible turns |15/36|18/25|
| Unchanged distance on feasible turns |0/36|5/25|
| Format rejection on feasible turns |11/36|0/25|
| First loss of feasibility: distance increase |9/16|12/16|
| First loss of feasibility: unchanged distance |0/16|4/16|
| First loss of feasibility: format rejection |7/16|0/16|
| Same action immediately after native no-op |1/3|15/29|
| Another rejection immediately after format rejection |8/29|not applicable|

All selected initial states are solvable within the frozen six-turn horizon.
Nevertheless, legal wrong-direction actions exhaust available slack, including
in12/16 TERSE episodes. The null therefore cannot be explained solely by rich
format rejection or by an initially impossible horizon. Repeated native no-ops
occur despite explicit prior-action/state feedback in the next prompt.

The no-op-following denominators exclude final turns, and include prefixes that
already cannot finish. A different next action is not automatically a useful
correction. Feasible-turn counts are separated to avoid treating late activity
as still capable of rescuing the episode. Conditioning on arm-generated states
precludes interpreting these fractions as randomized causal contrasts.

## Implication for the next decision

Treat basic observation-to-action interpretation as unresolved in this actor
and representation. Fluent text is not sufficient evidence of grounded action
selection. A future prerequisite-feedback experiment can distinguish initial
action competence from use of feedback; these data do not authorize changing
or rerunning the closed Taxi recipe, and do not prove that a new environment
will work. The existing successor proposal remains the new orchestrator's
decision. No attribution to the birth adapter versus the frozen base is possible
without that comparison. No H1/H2 or retained learning claim follows.

## Reproduce and checks

Run `python3 research_notes/analysis/2026-09-14_seq267_feedback_diagnostic.py`.
Its JSON contains per-episode first infeasibility and source bindings. Assertions
check complete matched identity, initial distances,192 observation/history and
transition records, parser errors, final states, and unchanged failures.
An independently written reverse-graph BFS also matched all32 initial distances
and first infeasible turns across192 transitions; this was a CPU cross-check by
the same analyst, not independent-person review or a new native oracle test.
