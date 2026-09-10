# Exploratory v6.1 result block

Date: 2026-09-07 UTC

Status: manuscript-side staging note, not a confirmatory result and not a
source for the frozen architecture deliberation. Do not paste claims into
`main.tex` without the final terminal audit and the paper's claim gate.

## Candidate result paragraph

Before the prospective one-parent/one-child experiment, we ran a deliberately
rough 1,024-episode CompilerGym lifetime to expose writer failures. The run is
not confirmatory: its finite program curriculum repeats, its birth prompt
contains a four-pass action example, generation is not fully counter-seeded,
one life suffered typed-action dialect drift, and the original split and
waking-brief resources are not suitable for a superiority claim. Nevertheless,
the sealed adapter-on/off checkpoints provide a useful positive control and a
sharp failure mechanism. In two surviving lives, adapters improve normalized
paired lifetime AUC by 0.0308 and 0.0447 through episode 896 and win 27/28
paired cuts. At episode 896, the gains are 0.0470 and 0.0567 and persist under
a one-action cap. Yet each adapter has zero marginal gain from actions 2--16:
98.1% and 94.8% of its actions repeat one life-specific routine. Corpus audits
explain the behavior. The top three action targets constitute 83.3% and 96.1%
of the respective sleep-896 corpora, and in the more concentrated life no new
normalized action target appears from sleep 672 through 896. Thus naive
on-policy consolidation can transport a useful supplied procedure while
failing to improve—and eventually suppressing—the investigation policy. A
third life supplies the complementary failure: useful latent action content
survives while self-training corrupts the strict typed-action dialect. These
failures motivate the prospective writer's fixed opportunity slots, equal
target exposure, native response-only loss, low-rank/low-heat calibration,
format canary, and separate measurement of value and investigation quality.

## Candidate compact table

| exploratory life, ep896 | adapter on | adapter off | paired gain | dominant action | unique/action | best-of-1 = best-of-16 |
|---|---:|---:|---:|---:|---:|:---:|
| B0 | 0.523262 | 0.476267 | +0.046995 | 154/157 (98.1%) | 3/157 (1.9%) | yes |
| B1 | 0.529087 | 0.472356 | +0.056732 | 146/154 (94.8%) | 7/154 (4.5%) | yes |

Descriptive paired lifetime summary through episode 896:

| life | positive paired cuts | cuts | normalized trapezoid AUC gain | mean paired gain |
|---|---:|---:|---:|---:|
| B0 | 13 | 14 | +0.03077 | +0.03219 |
| B1 | 14 | 14 | +0.04474 | +0.04409 |

### Sealed episode-960 plateau extension

Both surviving lives later sealed complete episode-960 on/off pairs. B0's
paired gain is `+0.053069` and B1's is `+0.058894`; under a one-action cap the
gains are `+0.063425/+0.066376`. This does not extend the learning claim:
each adapter-on value is exactly unchanged from episode 896, while 258/265
combined episode-960 on-adapter actions (`97.4%`) follow each root's dominant
six-pass routine. B0 and B1 converge to different six-pass extensions of the
same four-pass opening supplied in the birth prompt. The clean description is
useful taught-procedure transport followed by local policy fixation, not
discovery, learned THINK, or continued late-life improvement.

| exploratory life, ep960 | adapter on | adapter off | paired gain | first-action gain | dominant share |
|---|---:|---:|---:|---:|---:|
| B0 | 0.523262 | 0.470193 | +0.053069 | +0.063425 | 139/142 (97.9%) |
| B1 | 0.529087 | 0.470193 | +0.058894 | +0.066376 | 119/123 (96.7%) |

## Figure recommendation

Use a two-panel diagnostic, not a headline performance figure:

1. adapter-on/off held-out value versus lifetime for B0/B1/B2, with B2's
   strict-versus-permissive action-channel split explicitly marked; and
2. dominant-action share and unique-action/action for the matching probes or
   sleep corpora.

The visual claim is: a value curve can rise while the investigation policy
collapses. It should appear as motivation/ablation evidence after the clean
prospective result, or as the principal negative mechanism result if the
headline gate fails. It must not be described as novel strategy discovery,
learned THINK, strong-baseline superiority, or evidence for parenting.

## Reproduction

Read-only analyzer:
`research_loop/advisory/analyze_fable_v61_probe_actions.py`

Primary audit:
`research_loop/advisory/20260907_fable_v61_late_life_fixation_followup_v3.md`

Episode-960 two-root receipt:
`research_loop/advisory/20260907_fable_v61_two_root_ep0960_followup_v5.md`
