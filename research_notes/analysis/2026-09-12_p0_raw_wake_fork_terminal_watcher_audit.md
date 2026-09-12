# P0 raw-wake lesson-versus-sham fork: independent terminal watcher audit

Date: 2026-09-12. Status: **terminal independent watcher audit** of SEQ-075,
controller 77998, root
`astra_P0_raw_wake_fork_seed0_20260912_attempt1`. This audit applies the
result-blind interpretation rules committed before the outcome in
`2026-09-12_p0_raw_wake_material_fit_probe_audit.md`. It did not run a model,
use a GPU, alter builder code, or rescore answers.

## Verdict

The result is **no lesson utility at this resolution**. All four conditions
solve 0/16 mini-Sudoku boards on their first ACT. Both fitted adapters reduce
the native partial score relative to their identical OFF baseline:

| Condition | First-ACT solves | First-ACT native mean | ON - OFF |
|---|---:|---:|---:|
| Lesson OFF | 0/16 | 0.112500000 | -- |
| Lesson ON | 0/16 | 0.047500000 | -0.065000000 |
| Sham OFF | 0/16 | 0.112500000 | -- |
| Sham ON | 0/16 | 0.010546875 | -0.101953125 |

The score difference-of-gains is +0.036953125 and the solve
difference-of-gains is zero. Under the precommitted rule this is **relative
contrast without a useful lesson**: the lesson adapter harms less than the
sham adapter; it does not improve the child. It must not be reported as
parenting, thought-to-action transfer, or successful amortization.

## Independent recomputation and custody

I extracted the committed terminal capsule and recomputed the endpoints
directly from the 64 raw episode ledgers, selecting their `kind == "act"`
rows rather than accepting the supplied aggregate. Every cell contains 16
unique episode IDs and 16 measured ACTs. The raw score sums are 1.8, 0.76,
1.8, and 0.16875 in table order, reproducing the four means above; none of the
64 scores equals 1.0. There is exactly one ACT per episode, so no later-action
or native-best rescue exists.

The two OFF cells are byte-identical after sorting by episode over episode ID,
action, score, prompt hash, output hash, and generation seed. Thus the
observed OFF gap `B` is exactly zero, not hidden generation noise. The frozen
plan hash recomputes to
`2df054868b588c857054d84d5355a9d894e7a2588107ac72810950f45c783081`.
Both training manifests bind the predeclared corpus hashes, rank 8, learning
rate 1e-4, three epochs, seed 0, batch size 1, no packing, maximum length
4096, exactly 96 updates, and zero nonfinite batches. They also preserve the
unequal supervised doses: 4,289 lesson versus 5,360 sham target tokens.

The committed capsule, analysis, terminal receipt, and raw prompt review
recompute respectively to their stated SHA-256 values
`3508c27cf9832f25c059d96b990ff285cf6011bad2714aa8e2d175ad8a368fd6`,
`a5a9d752c39a22cd3edc2ba3de2d33d79e436b85b7a5885452cebb085bb0ecba`,
`9bd381819743d7f3cf7a93b8b851cbe79d30f1e69de2557c3c1f527d202c653d`,
and `07e500afab242e897ec182c496f2e234f513f2085db593771ad586e71975b99a`.
The separate raw review reports zero question-hash, birth-prefix, or exact
reference-prompt mismatches across all 64 observations, with the fixed
400-token, temperature-0.7 generation setup. The terminal receipt records
root completion at 11:43:29 UTC, controller absence at 11:43:38 UTC, and
successful owned-group and GPU-release checks for all eight workers. This
proves terminal capture and bounded run custody; it does not independently
authenticate the remote model origin or locally rehash the omitted adapter
weights.

## Claim boundary and consequence

This is one optimizer seed, one historical recipient/material realization, a
reused 16-board development panel, unequal teacher and target-token doses,
and an evaluation of only one of the seven source families. The raw targets
mostly precede task feedback and contain no current-action outcome, so the
result cannot reject parenting or experiential SLEEP. It says only that
fitting these two particular historical raw child-continuation packages did
not improve first-action mini-Sudoku behavior and substantially degraded its
partial score.

Do not spend more GPU hours repeating this unchanged package. The next
parenting diagnostic should first establish, without a write, that a frozen
teacher's prospective process instruction changes useful observable behavior
relative to a genuinely token-matched sham. The paper-relevant writer path
still requires mechanically joined action-outcome evidence, useful-versus-
corrupted controls, new material-generation seeds, and a fresh panel.
