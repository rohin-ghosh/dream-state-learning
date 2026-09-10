# Fable v6.1 late-life fixation follow-up v3

Date: 2026-09-07 UTC

Status: exploratory, read-only analysis of an in-flight legacy run. This note
does not authorize or alter any model call, adapter fit, benchmark execution,
GPU job, source-bound proposal, or scientific claim. The v6.1 run retains its
known split, provenance, prompt, and generation confounds and is not
confirmatory evidence.

## New sealed boundary

`L_B_seed0` completed `wake_0880_0888.json` while its original process remained
live. All eight episode summaries named the same best action:

```text
-mem2reg, -sroa, -gvn, -simplifycfg, -licm, -instcombine
```

Correctly delimiting the corresponding eight episode runs in the immutable
ledger gives 187 actions but only seven distinct action strings. The six-pass
string accounts for 165/187 actions (88.2%); a related eight-pass string
accounts for another 16/187. There were two invalid actions, one blank action,
and 36 actions without an attached prediction. Thus the actor is still
functional and receives useful scores, but its proposal distribution has
nearly collapsed onto one transported routine.

## Paired adapter-off localization at episode 832

The already-sealed episode-832 probe provides a cleaner paired diagnostic.

| condition | mean held-out score | actions | unique action strings | unique/action | invalid |
|---|---:|---:|---:|---:|---:|
| adapter on | 0.512861 | 136 | 2 | 0.0147 | 0 |
| adapter off | 0.476267 | 103 | 28 | 0.2718 | 57 |

For adapter-on, the first action already attained the final per-episode best
on all eight probes: mean best-of-first-{1,2,4,8,16} was identically 0.512861.
Adapter-off improved with search from 0.459837 at one action to 0.476267 by 16
actions. Adapter-on therefore beats adapter-off even under a one-action cap,
so the late checkpoint contains real action-policy transport rather than a
mere action-volume advantage. But the zero marginal value of later actions
and 2-versus-28 action vocabulary show that it did not learn a better
investigation procedure. It learned an immediately useful routine so strongly
that almost all later search became repetition.

This corrects two tempting over-interpretations:

1. The effect is not evidence of novel compiler-strategy discovery: the
   ancestor bootstrap supplied the four-pass prefix, and sleep extended and
   reinforced that scaffold.
2. Better held-out value is not by itself evidence of learned THINK or
   meta-intelligence. The same value gain can coexist with a less adaptive
   proposal distribution.

## Fixation and saturation across lifetime

A read-only pass over every currently sealed paired probe shows that the
collapse begins with the first write rather than appearing only at episode
832. Before any sleep, unique-action/action was 0.560 for B0 and 0.435 for B1.
At episode 64 it was 0.154 and 0.031 adapter-on, versus 0.443 and 0.407 for
the paired adapter-off probes. Later adapter-on checkpoints usually remain
below 0.10 while adapter-off usually remains above 0.27.

B1 makes the saturation especially visible. Its adapter-on mean is exactly
0.529087 at each sealed probe from episode 384 through episode 832, while the
cumulative sleep corpus and fitting continue to grow. At those checkpoints,
the most frequent action accounts for 89.8% to 98.2% of all actions. B0 is
less stable but shows the same qualitative compression: its most frequent
action reaches 99.4% at episode 704 and 86.0% at episode 832.

This equality is not rounding coincidence. The final eight-program score
multiset at every B1 checkpoint in that interval is the deterministic result
of the same six-pass routine
`-mem2reg,-sroa,-gvn,-simplifycfg,-instcombine,-constprop`. At episodes 384,
512, 640, 704, 768, and 832, that routine is already the first action for all
eight probes. At 448 and 576, a weaker or truncated first form appears on one
or two probes and later actions recover the same routine and terminal vector.
Continued sleeps therefore reproduce one fixed policy rather than changing
the held-out behavioral frontier.

This is a useful negative flywheel result. Repeated writes can rapidly
transport a robust policy and reduce invalidity, yet additional lived data
need not increase competence once the writer repeatedly reinforces the same
high-reward routine. The missing signal is not merely more experience; it is
selection and rendering that rewards informative deviations, conditional
scope, failure-driven revision, and improvement in the investigation policy.
That is precisely what one-parent process correction plus the registered
parenting-by-deployment-writing interaction is meant to test.

The sealed sleep-864 corpora directly support this mechanism. B0 contains
1,195 parsed `ACT` lines; its four-pass and six-pass routines account for
437 and 539 respectively, or 976/1,195 (81.7%) together. B1 contains 1,076
parsed `ACT` lines; three orderings/extensions of the same routine account for
601, 296, and 136, or 1,033/1,076 (96.0%) together. The corresponding adapters
were clean-base rank-16 fits at learning rate `1e-4` for three epochs over
approximately 768k and 758k training tokens. The behavioral collapse therefore
mirrors the writer's target-frequency distribution; it is not evidence that
rank alone caused the pathology.

The complete sleep series shows path-dependent reinforcement rather than one
anomalous final corpus. In B1, the three most frequent action targets rise
from 84.6% of parsed `ACT` lines at sleep 32 to 93.3% at sleep 64 and remain
about 96% late in life. Unique-action/action falls from 0.269 to 0.038, and
the absolute unique count remains frozen at 41 from sleeps 672 through 864
while the corpus continues growing. B0 is less extreme: its top-three share
stays roughly 75--84%, unique-action/action falls from 0.219 to 0.111, and the
dominant target changes from the supplied four-pass routine to its six-pass
extension at sleep 512 before persisting. The seed difference matters: the
failure is a general concentration pressure with life-specific attractors,
not one universal fixed string.

The confirmatory writer already closes this defect rather than reacting to it
post hoc: at most one earliest-law-eligible `THINK_TO_ACT` target can fill each
fixed opportunity slot, every filled or rehearsal slot has equal four-exposure
weight, response suffixes are normalized before slot averaging, rank is eight,
and the lowest passing learning rate is selected from a prospective neutral
calibration. The new evidence validates why those constraints are necessary;
it does not require changing their frozen bytes.

## Episode-896 paired replication

After sleep 896 committed, B0's next paired probe strengthened the same
conclusion. Adapter-on scored 0.523262 versus 0.476267 adapter-off. On-adapter
used 157 actions but only three distinct strings; the six-pass routine
accounted for 154/157 (98.1%). Off-adapter used 86 actions and 29 distinct
strings. The on-adapter mean was identical under best-of-first-1, 2, 4, 8,
and 16 actions, while off-adapter rose from 0.459837 at one action to 0.476267
at 16.

The on-adapter increase from episode 832 (`0.512861`) to 896 (`0.523262`) did
not introduce a better action family or a search benefit. The same six-pass
routine was now applied successfully on all eight probes rather than sharing
the panel with its weaker four-pass prefix. This is improved coverage of one
compiled policy, not expansion of the behavioral frontier. It remains useful
procedural learning, but it is the wrong evidence for learned investigation.

B1 independently reproduces the same separation at episode 896 with its own
life-specific attractor. Adapter-on scored 0.529087 versus 0.472356 off. Its
six-pass `...,-instcombine,-constprop` routine accounted for 146/154 actions
(94.8%); seven strings appeared in total, four were invalid, and 28 actions
lacked a prediction. Adapter-off used 77 actions and 31 distinct strings. As
for B0, adapter-on best-of-first-{1,2,4,8,16} is identically 0.529087, whereas
adapter-off rises from 0.459837 at one action to 0.472356 at 16.

At this common checkpoint the two adapters therefore produce real paired
level gains of 0.046995 and 0.056732, each under a fixed-one-action cap as
well as the full panel. But both have zero marginal gain from later actions
and overwhelmingly replay different learned routines. The reproducible
result is **competence transport with policy concentration**, not a positive
lifetime-learning slope or a learned investigation strategy.

The complete currently sealed paired curves reject the stronger claim that
these two writers are simply harmful. Across episodes 64--896, B0 is
adapter-positive at 13/14 cuts and has normalized trapezoidal on-minus-off
AUC `+0.03077`; B1 is positive at 14/14 cuts with AUC `+0.04474`. Their mean
paired differences are `+0.03219` and `+0.04409`. These descriptive effects
remain exploratory because v6.1 has known target-split, prompt-provenance,
generation-seed, and waking-brief confounds. Within those limits they are a
useful positive control: LoRA consolidation can transport a supplied routine
to the held-out panel. The distinct negative control is completed life B2,
whose content survived beneath a self-reinforcing typed-action dialect loss.
The aggregate lesson is neither “LoRA does nothing” nor “the flywheel works”:
naive self-training can improve the actor's level, then either lock it onto a
routine or corrupt the action channel instead of improving its learning rate.

## B2 action-channel transition

The same analyzer now measures the complementary B2 failure in its training
distribution. At sleep 32, all 30 detected action-marker lines begin with the
executor's canonical bare `ACT:` form. Decorated forms then accumulate while
the absolute stock of strict rows nearly stops growing. By sleep 320 there are
318 strict and 236 decorated marker lines, so strict share is 57.4%; this is
the same checkpoint where strict probe behavior falls abruptly from near
parity at episode 256 (`0.4637` on versus `0.4702` off) to `0.0511` on versus
`0.4821` off. By terminal sleep 1024, only 352/1,449 detected marker lines
(24.3%) are strict, 354 begin with Markdown headings such as `### ACT:`, and
1,097 are decorated or embedded forms. The terminal adapter emits only one
strictly parsed action across eight probes and scores `0.0511`, while the same
checkpoint adapter-off scores `0.4859`.

This is a distributional motor-channel failure, not erasure of all action
content: the prior permissive saved-byte diagnostic recovered useful latent
actions. A commit-time canary must therefore test the actual native action
envelope after every fit and quarantine a candidate adapter on strict routing
failure. Training loss or semantic inspection alone cannot certify the write.
The confirmatory protocol already requires this transactional non-erasure
gate and never relaxes the parser to rescue a failed adapter.

## Consequence for the confirmatory one-parent/one-child protocol

The registered separation of proposal quality, typed routing, valid/distinct/
informative actions per generated token, and held-out value is necessary, not
decorative. Parenting must teach evidence-responsive investigation and the
writer must preserve it; otherwise `P1` can win by compiling one nursery-born
routine while losing the claimed ability to learn during deployment.

The current proposal already defends against this failure with a target-blind
nursery, no example deployment action in the shared birth state, parent
deletion, `P0/P1/U0/U1` interaction, sealed entry checkpoint, and separate
proposal/routing metrics. No bound proposal byte changes as a result of this
exploratory follow-up.

## Artifact receipts

Remote root: `/localhome/local-rohing/v6_out/L_B_seed0`

- `wake_0880_0888.json`:
  `50e39ec349c761cc6b560476f19fea2b03d843c1f0bd95f6c36bacbd1e5aa5ac`
- `probe_ep0832.json`:
  `b97caf750de1f7533cab33fec8043a439aaadbef8e2a7ea8a24b3be2f491dbbd`
- `probe_ep0832.ledger.jsonl`:
  `1182a28daf63a93652d038a41a1f8fc6e75165db39b79ed56aef2cbc8c017d4f`
- `probe_ep0832_adapterOFF.json`:
  `99b755c096421dd3e52a86d8348602af8cc6cd74f6474f013c45c77764df6c6a`
- `probe_ep0832_adapterOFF.ledger.jsonl`:
  `f7ae7525cf31787a4a238fbff549900339c667e1b456db52879a5fae32358728`
- `probe_ep0896.json`:
  `71b8824d23f9f2c5e393254c2193877490b6244bada145012255128d3abcbfa4`
- `probe_ep0896.ledger.jsonl`:
  `6e8d26197649c0a0501536b669309ada428a6856463dedd221ace318f5cb65c6`
- `probe_ep0896_adapterOFF.json`:
  `0073870632884ac8759162d55b26854ae8f4e39b75a6672c86c2ef02dabf64b0`
- `probe_ep0896_adapterOFF.ledger.jsonl`:
  `d0f887bbf842647d52c72187a06850891a90b612c52ab0149c9fa1b28b1ec764`

B1 remote root: `/localhome/local-rohing/v6_out/L_B_seed1`

- `probe_ep0896.json`:
  `a0aa44816e2cf5ba97c332f4e9ac36c4f2353eafd74c587deaa5aff134ab75c7`
- `probe_ep0896.ledger.jsonl`:
  `8e6767d208d276c7673f4dda0a91a132881072ec601accc7ea91be52b701c3c2`
- `probe_ep0896_adapterOFF.json`:
  `38a1ac2d9f33b0aa62a971e366b427754ab70a40e3d5b31ff20c7a999b00665b`
- `probe_ep0896_adapterOFF.ledger.jsonl`:
  `e8efab410fe1e1923f2ab8b87bf0d2fb2c29e8b106f4cb92c12cc8d98e6761e1`
