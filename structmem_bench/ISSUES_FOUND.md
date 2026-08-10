# Issues found (self-review, pre-red-team) — to batch-fix after red-team reports

Holding fixes until red-team agents finish, to avoid version skew during their runs.

## ISSUE A — relational AP diluted by candidate-pair explosion (MEDIUM-HIGH)
`memory.candidate_pairs` enumerates all co-occurring pairs. With the one-shot detail
pool (n_episodes × oneshot_per_episode facts, each appearing once), many spurious
single-co-occurrence pairs enter the candidate set, diluting relational AP
(0.30±0.24 here vs 1.0 in exp3's small clean universe). This is the exp3 caveat
("enumerating relations doesn't scale") biting concretely.
Candidate fixes: (a) restrict candidates to pairs co-occurring ≥ min_cooc times;
(b) report relational AP only over pairs among "retained" facts at budget;
(c) report a rank-of-true-relations metric robust to candidate-set size;
(d) acknowledge as a measured LIMITATION (enumeration doesn't scale → motivates
learned relational keys). Likely: (a)+(d).

## ISSUE B — tie-breaking in average_precision leaks fact-index position (HIGH)
Facts are laid out CONTIGUOUS by type (structural at low indices). `average_precision`
uses a STABLE argsort, so TIED scores break by original index → structural (low index)
ranks above detail (high index) among ties. Methods with many ties (esp. `surprise` =
1/(count+1): all count=1 facts tie) get SPURIOUSLY inflated structural AP via position.
This is a real label-position leak through the metric.
Fix: decorrelate fact index from type — apply a seeded column permutation in
`tasks.generate` so index ⊥ type (kills the leak on every code path, not just AP).
Verify surprise AP drops after the fix.

## To reconcile with red-team findings (redteam_1/2/3) when they land.
