# Lower-learning-rate writer comparison: terminal independent audit

**Verdict: changing learning rate alone does not make the writer selective.**
Both matched lower-rate fits acquired the intended dose-16 frame association,
but both remained `frame-habit` writers because their effects spilled across
controls by roughly ten times the registered maximum. Do not spend another
cell on an LR-only sweep. The next information-bearing tests are the semantic
W0 conditional carrier and the useful-versus-corrupted behavioral-material
control.

This is a one-bank, one-optimizer-seed diagnostic over externally constructed
oracle material. It is not child-authored SLEEP, a clean lineage, W0/W1, or a
lifetime-learning result.

## Terminal custody

Both controllers are absent and sealed `WORKER_COMPLETED`:

| LR | root suffix | completed UTC | controller receipt SHA-256 | report SHA-256 |
|---:|---|---|---|---|
| `3e-5` | `astra_A1_lowerlr_bank0_ts2_3e5_20260912_attempt1` | `10:39:08` | `091a5766...8993` | `64f5937a...cbc9` |
| `1e-5` | `astra_A1_lowerlr_bank0_ts2_1e5_20260912_attempt1` | `10:39:04` | `c7d190a2...e20d` | `2f6a81a7...99be` |

Each fit used the exact same 12,924-row bank-0 oracle corpus
(`f2388eaf...c37d`), frozen Qwen2.5-7B-Instruct base, rank 8, training seed 2,
three epochs, 9,693 optimizer steps, 749,985 input tokens, and 711,213
supervised tokens. The historical `1e-4` baseline was not retrained. New
`train_meta.json` SHA-256s are `3ca5f12c...afce` (`3e-5`) and
`c577740e...512` (`1e-5`). Native evaluation used all 1,313 original cues at
lambda 1. The identical OFF frame probability, `0.2596499`, is an additional
runtime-consistency check.

## Result

The predeclared selective-binding gate requires a positive lower confidence
bound for `I_d_frame` **and** mean frame spill no greater than `0.03`.

| learning rate | `I_d_frame` (95% paired-owner interval) | dose-16 frame `P`, OFF -> ON | frame spill | spill / allowed | dose gate | label |
|---:|---:|---:|---:|---:|---|---|
| `1e-4` historical | `1.921` `[1.203, 2.683]` | not re-reduced here | `0.4155` | `13.85x` | historical | fails |
| `3e-5` | `3.078` `[1.991, 4.163]` | `.260 -> .920` | `0.3936` | `13.12x` | pass | `frame-habit` |
| `1e-5` | `1.140` `[.520, 1.816]` | `.260 -> .617` | `0.2964` | `9.88x` | fail by `.0010` | `frame-habit` |

At `3e-5`, spill components were `.255` on unexposed owners, `.317` on
look-alike frames, and `.609` on exposed bicycles. At `1e-5`, they remained
broad and nearly uniform: `.284`, `.297`, and `.308`. The `1e-5` dose rise was
`.09898` against the registered `.10` minimum. Both writers drove abstention
probabilities effectively to zero (`<=3.25e-7` on the reported control
groups), another signature of a global completion habit rather than scoped
memory.

## Interpretation

Lower heat trades effect strength against spill but does not change the kind
of thing learned. The `3e-5` fit actually acquired the association more
strongly than the `1e-4` baseline while retaining almost all of its spill. At
`1e-5`, both acquisition and spill weakened, yet spill was still almost ten
times the acceptance threshold and abstention vanished. This is a movement
along one unselective-habit curve, not evidence that a sufficiently small LR
will uncover a selective regime.

The result rejects the narrow explanation that the existing writer fails
mainly because `1e-4` is too hot. It points upstream to conditional material,
contrast structure, and the model's ability to carry a multi-key action
surface. Therefore:

1. retain these rates as diagnostic evidence, not recipe candidates;
2. stop LR-only tuning on this oracle frame corpus;
3. prioritize semantic W0, where success requires complementary actions under
   distinct keys rather than one globally reusable completion;
4. use the mini-Sudoku useful-versus-corrupted test only as a bounded behavior
   positive control, with its independent audit limitations; and
5. do not infer anything yet about authentic action-outcome SLEEP or parenting.

