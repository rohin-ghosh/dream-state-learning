# Fable v6.1 two-root episode-960 follow-up v5

Date: 2026-09-07 UTC

Status: exploratory, read-only saved-artifact analysis of an in-flight legacy
run. No model, tokenizer, compiler, adapter, benchmark, process, or GPU
operation was launched, stopped, or changed. This supports no confirmatory or
manuscript claim and inherits all split, prompt-provenance, generation-seed,
writer, repeated-program, and post-hoc-analysis limitations from the earlier
v6.1 audits.

## Newly sealed root

`L_B_seed1` now has complete adapter-on and adapter-off probe ledgers at
episode 960. The unchanged saved-artifact analyzer reports:

| condition | held-out mean | actions | distinct actions | dominant share | invalid | unpredicted |
|---|---:|---:|---:|---:|---:|---:|
| adapter on | 0.529087 | 123 | 4 | 119/123 = 96.7% | 2 | 19 |
| adapter off | 0.470193 | 86 | 31 | 37/86 = 43.0% | 19 | 4 |

The paired on-minus-off difference is `+0.058894`. Under best-of-first action
caps `{1,2,4,8,16}`, the corresponding differences are
`{+0.066376,+0.069250,+0.061398,+0.058894,+0.058894}`. The gain therefore
exists on the first proposed action and is not caused by dispatching more
actions.

The on-adapter dominant action is
`-mem2reg,-sroa,-gvn,-simplifycfg,-instcombine,-constprop`. It is distinct
from seed 0's six-pass routine but extends the same four-pass opening supplied
in the birth prompt. This may reflect selection and transport of a local
extension; it does not establish novel strategy discovery.

## Plateau check

The complete seed-1 episode-896 pair was analyzed with the same code. Its
adapter-on score is exactly the same saved value as episode 960:
`0.5290871209234732`. The dominant routine share rises from `146/154 = 94.8%`
at episode 896 to `119/123 = 96.7%` at episode 960, while distinct on-adapter
actions fall from seven to four. Another 64 repeated programs and two sleeps
therefore did not improve held-out value; they further concentrated the
policy.

## Two-root late-life synthesis

Seed 0 and seed 1 now independently show the same qualitative late-life
state:

- adapter-on beats its contemporaneous adapter-off diagnostic by
  `+0.053069` and `+0.058894` (mean `+0.055981`);
- the one-action-cap differences are `+0.063425` and `+0.066376` (mean
  `+0.064900`);
- across the two episode-960 adapter-on ledgers, 258 of 265 actions (`97.4%`)
  are each root's dominant six-pass routine; and
- each root's episode-960 adapter-on value is unchanged from episode 896.

This is useful evidence that repeated LoRA sleep writes can transport and
stabilize a useful taught procedure while collapsing exploration into a local
policy plateau. It is evidence against describing this legacy mechanism as
continually improving THINK. It does not test parenting, parent removal,
learning-to-learn, novel hypothesis generation, connected experiential
knowledge, or superiority to a validated active-text baseline.

The design consequence is narrow and prospective: the one-parent experiment
must score both held-out value and information-seeking diversity per generated
token, and its parenting teachability canary must require a practiced
parent-absent disposition rather than reproduction of a supplied routine.

## Artifact receipts

Remote root: `/localhome/local-rohing/v6_out/L_B_seed1`

- episode-896 adapter-on ledger:
  `8e6767d208d276c7673f4dda0a91a132881072ec601accc7ea91be52b701c3c2`
- episode-896 adapter-off ledger:
  `e8efab410fe1e1923f2ab8b87bf0d2fb2c29e8b106f4cb92c12cc8d98e6761e1`
- episode-960 adapter-on ledger:
  `a898bd977bc41478e76d8781ef692945c4ebfd1eac98f9aa8e02c8dcc3171b32`
- episode-960 adapter-off ledger:
  `9a9386faf99946dab065bcad50265309532137c0a9d3b88058bd55de68984c67`

Seed-0 episode-960 receipts and values are in
`20260907_fable_v61_ep0960_followup_v4.md`.

Reproducer:

```text
python3 research_loop/advisory/analyze_fable_v61_probe_actions.py \
  --root <saved-root> --seeds 1 --checkpoints 896,960 --summary-only
```
