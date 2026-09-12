# P0 raw-wake material and lesson-versus-sham fit: independent watcher audit

Date: 2026-09-12. Status: **result-blind watcher audit**. The audit was first
committed at 11:24 UTC, three minutes after the frozen controller launched and
before this watcher inspected any fit or probe outcome. It is therefore not a
prospective registration and cannot amend the builder's frozen primary
endpoint. It does not change builder code, run a model, use a GPU, or authorize
a claim.

## Verdict in one paragraph

The committed export is a well-custodied, executable **development material
fork**. It is reasonable to run once as an engineering utility diagnostic. It
is not an action-outcome learning assay, a SLEEP/compile assay, or an isolated
parenting experiment. Thirty-one of the 32 paired inputs are identical after
teacher deletion and almost every target is the child's first pre-feedback
wake, so the cleanest estimand is narrow but useful: does fitting the raw
continuations produced under this fixed record-lesson package alter later
parent-free actions more usefully than fitting continuations produced under
this fixed active-sham package? A positive answer would show amortization of a
teacher-conditioned behavior distribution into a LoRA for this one historical
material realization. It would not show learning from consequences, semantic
parenting in isolation, or population-level repeatability.

## Capsule integrity and exact material

I independently unpacked
`receipts_20260912/astra_raw_wake_export_20260912.tgz` and obtained archive
SHA-256 `1fbe9018df4b0251fdda0266c08c34d87774ddbdf5968edfd4db32f18406ba43`.
All eight payload hashes in `artifact_hashes.json` recomputed exactly; zero
mismatches. The frozen corpus identities are:

- lesson corpus: `47575250b9c6a084839824b918899211cdeae4d65c91a2c43002633b9af4c6e2`;
- sham corpus: `8c55713acd1a899a8c7f35f92757f132d6950acd7afc57a5cdbd036e776732b9`;
- selection: `a93984396bfd3d76d5fb9cbb122c59528be94d819e5013e04244296ff0e7e6a8`.

Both arms contain the same 32 episode IDs in the same seven-family order:
countdown 5, mini-Sudoku 5, futoshiki 5, knights/knaves 5, ARC-1D 4,
Sokoban 4, and Kakurasu 4. The exporter binds each raw generation to its
request, seed, occurrence, parsed ACT sequence, measured ledger event and
immutable source hashes. It removes the teacher-bearing prompt head, masks all
remaining context labels, preserves the exact child target plus EOS, and
reports no truncation. These facts support source custody and exact trainer
input construction. They do **not** certify the truth or usefulness of the
child's prose.

## What is actually being trained

This corpus is better described as **teacher-effect distillation through raw
child continuations** than as experiential consolidation:

- lesson has 31 tick-1 targets and one tick-2 target; sham has 32 tick-1
  targets;
- 31/32 cleaned conditioning contexts are byte-identical across arms;
- none of the 32 raw targets are identical across arms, and only 1/32 first
  executed actions is identical;
- actual current-action outcomes are audit-only sidecar fields. They are not
  appended to the conditioning context or supervised target;
- selected targets contain 34 executed actions in lesson and 37 in sham, but
  the whole raw chunks also include unexecuted text, guesses, copied clock or
  score-like prose, and statements that have no truth certificate;
- only 2 lesson chunks and 3 sham chunks contain an accepted action. Mean
  within-chunk best source score is 0.1026 versus 0.1199;
- all five selected mini-Sudoku chunks in each arm are unsolved. Their best
  source scores are lesson 0.109/0/0/0/0.113 and sham 0/0/0/0/0.

The single unmatched context is lesson `rg/arc_1d/1439881` at tick 2 versus
sham tick 1. Its lesson input includes child notes and recalled prior ARC
material and is much longer. This does not invalidate a package-level
comparison, but it breaks an exact input-only-different-target description.

Consequently, a later behavior change can support "a LoRA imitated or
amortized these teacher-conditioned continuations." It cannot support "the
agent learned from the consequences of its actions": the relevant consequence
was never in the learned sequence. It also cannot support a DREAM/SLEEP claim:
there is no outcome-grounded selection, replay, paraphrase, contrast, or
cross-episode compilation in this export.

## Dose and content asymmetries

| Quantity | Lesson | Sham | Consequence |
|---|---:|---:|---|
| historical fixed teacher tokens/presentation | 203 | 158 | lesson is +45 tokens (+28.5%) |
| historical teacher presentations | 2,937 | 2,656 | realized childhood trajectories/dose diverged |
| nominal teacher-token presentations | 596,211 | 419,648 | lesson/sham ratio 1.421; descriptive product only |
| selected examples / proposed updates | 32 / 96 | 32 / 96 | sequence/update count matched |
| supervised target tokens | 4,289 | 5,360 | sham is +1,071 (+25.0%) |
| supervised target-token passes over 3 epochs | 12,867 | 16,080 | exact fitted target dose |
| zero-loss context tokens | 27,458 | 26,167 | lesson is +1,291 (+4.9%) |
| all input tokens | 31,747 | 31,527 | totals look matched only because offsets cancel |
| all input-token passes over 3 epochs | 95,241 | 94,581 | near-equal total hides target asymmetry |
| chunks with PREDICT / NOTE / RECALL | 30 / 24 / 3 | 32 / 20 / 5 | learned dialect mixtures differ |

With batch size 1 and one sequence per update, 96 updates per arm match
sequence-level optimizer opportunity, not supervised-token content or effective
gradient dose. Longer targets do not translate mechanically into 25% more
weight change because loss is token-averaged, but the target-token asymmetry is
still part of the treatment and must be reported. Likewise, the teacher-dose
difference is a mediator of the fixed packages but a confound for any claim
that isolates lesson semantics. Post-hoc truncation or repetition would create
a different corpus, not repair this historical comparison.

The active sham is not inert: it explicitly advises considering constraints,
relationships and alternative possibilities. The contrast is therefore
"measured-record lesson package versus generic reasoning lesson package," not
"teaching versus no teaching."

## Evaluation contamination and scope

The builder's exact frozen panel is mini-Sudoku IDs 1900050--1900065. It is
already an openly used development panel: its base, useful and wrong-board
outcomes have been examined across three optimizer seeds, and the decision to
advance this raw-wake probe was made after those outcomes. It is valid for fast
diagnosis, but no result on it is confirmatory or untouched.

Native prelaunch validation establishes that all 64 historical source episode
IDs and the five selected mini-Sudoku question strings are disjoint from those
16 canaries. It also finds one reference-solution-grid overlap:
`rg/mini_sudoku/1189872` in the source and canary
`rg/mini_sudoku/1900061`. Keep the canary and disclose the overlap, as the
frozen plan does; do not call the panel wholly unseen-solution transfer. More
importantly, a one-family panel is mismatched to a seven-family training
mixture. A positive could be an ACT/format or Sudoku completion habit; a null
cannot reject utility in the other six families.

For a paper claim, freeze a new panel before fitting or inspecting outcomes,
audit puzzle/solution identities against both source arms, and repeat the whole
material-generation process on new schedule/generation seeds. Re-fitting this
same corpus under more optimizer seeds would establish optimizer stability,
not parenting repeatability.

## Result-blind analysis rule for the one-seed diagnostic

The frozen builder specification says there is no post-hoc success bar and
makes first-ACT exact solves the primary. The rule below preserves that order;
it is an independent interpretation discipline, not a replacement gate.

### Eligibility before reading ON results

1. Bind the three corpus/selection hashes above, exact 32-row IDs/order, base
   bytes, rank 8, learning rate 1e-4, three epochs, seed 0, batch 1, no packing,
   maximum length 4096, and 96 completed finite-loss updates per arm.
2. Record actual train manifests and confirm 4,289 versus 5,360 supervised
   target tokens. Do not rename the comparison dose-matched.
3. Verify the already frozen plan SHA-256
   `2df054868b588c857054d84d5355a9d894e7a2588107ac72810950f45c783081`,
   panel IDs 1900050--1900065, generation seed 0, seed salt 15420, one tick,
   temperature 0.7 and 400 wake tokens. Label the panel `development`.
4. Require both arms and all four fresh OFF/ON processes. Missing one arm is an
   incomplete comparison, not a win for the surviving arm.
5. The duplicate OFF paths use the same base, prompts and generation seeds.
   Require identical prompt hashes and report whether their first actions and
   scores are exact matches. If they differ, retain the observed OFF gap `B`
   and do not describe randomness as an adapter effect.

### Fixed estimands

For puzzle `i`, let `Y` be the native score of the first ACT, with missing or
invalid first ACT set to zero, and let `S` be exact solve (0/1). For each
endpoint compute:

```text
G_L = mean(lesson_ON - lesson_OFF)
G_S = mean(sham_ON   - sham_OFF)
B   = mean(lesson_OFF - sham_OFF)
D   = G_L - G_S = mean(lesson_ON - sham_ON) - B
```

Report the full vector for exact solves, first-ACT native score, first-ACT
validity, number of ACTs, and native best score. Exact solves remain the frozen
primary; first-ACT score is the higher-resolution diagnostic. Marker frequency
or changed prose is a mechanism diagnostic, never task utility.

Predeclare these interpretations:

- **Directional lesson-derived utility, exploratory only:** `G_L > 0` and
  `D > 0` on first-ACT score, at least one extra exact lesson solve (`G_L^S >=
  1/16` and `D^S >= 1/16`), and no first-ACT validity loss versus lesson OFF.
- **Partial-score shift only:** score conditions hold but exact-solve
  conditions do not. Say exactly that; do not promote it to solution transfer.
- **Generic/raw self-imitation:** lesson and sham both improve but `D <= 0`,
  or their gains are indistinguishable at the panel's resolution.
- **Relative contrast without useful lesson:** `D > 0` only because sham is
  harmed while `G_L <= 0`. This is not lesson utility.
- **Dialect change only:** output/marker/validity changes without positive
  world-score effects.
- **Harm or null:** report per arm; neither result refutes parenting because
  current targets are mostly pre-feedback, unsuccessful first wakes.

The actual run is source commit `a4feb0f775246ad065e421b8cb34fa9705268773`,
controller 77998, node-3 GPU 1, with lesson fit/OFF/ON followed by sham
fit/OFF/ON on the same reserved device. Sequential arm order and time are
therefore fixed rather than randomized and belong in the limitations.

The 16 puzzle cells are a fixed task panel, not 16 independent learned agents.
Do not quote an episode-level p-value or bootstrap interval as learner-level
uncertainty. A paired-board bootstrap may be shown only as conditional
development-panel sensitivity. The scientific replication unit must include a
new material-generation seed; ideally cross it with a new optimizer seed and a
fresh sealed task panel.

## Recommendation

**GO as one bounded diagnostic, NO-GO as headline evidence.** It is cheap and
can answer whether raw parent-conditioned continuations have any downstream
utility after parent deletion. Preserve every asymmetry rather than "fixing"
the historical corpus. Whatever it returns, the next paper-relevant step still
needs actual action+outcome sequences, a compiled useful-versus-corrupted
control, multiple independently generated lives, and a fresh evaluation panel.
