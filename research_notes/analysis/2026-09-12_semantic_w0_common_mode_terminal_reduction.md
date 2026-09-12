# Semantic W0 terminal reduction and causal-score contradiction

Date: 2026-09-12 UTC

Status: independent watcher-side reduction of the completed diagnostic run
`astra_semantic_writer_Q0_20260912_attempt1` plus raw validation of the
no-fit supplementary score repair
`astra_semantic_rescore_20260912_attempt1`. This is not a new fit, a repaired
gate, or a scientific promotion. It changes no builder source, job, model,
adapter, benchmark, or claim authority.

## Result in one sentence

Strict generation shows that the four rank-8 adapters did not learn the held
key-conditioned mapping (`0.500--0.578` balanced accuracy, only `1--5/64`
better than OFF). The original unequal-shape BF16 candidate scores are
invalid; a terminal equal-shape no-fit rescore repairs their causal
consistency and shows a large broad action-class shift plus only partial
conditional association. Exact-training generation is also at chance, so this
run does not qualify the writer: the recipe failed to create usable
key-conditioned associations rather than merely failing held-form extraction.

## Authoritative terminal facts

The node-3 run has `report.json` SHA-256
`31ea19f9d0c8807a30252340dc0582e829bb4ac6d1c438f712e590a909ad31af`
(`348402` bytes), all fourteen stages complete, controller `98756` absent,
and GPU 0 released. `RESOURCE.json` reports `1414.6955` seconds. Original-
source replay reproduces the report. The frozen label is
`OPTIMIZATION_INCONCLUSIVE`; its aggregate gates are:

```text
oracle_ok       true
interface_ok    true
binding_ok      false
optimization_ok false
spill_ok        false
```

All four adapters retain strict generation validity `1.0`, zero multiple
ACTs, zero truncations, and all eight native copy canaries. Their held-form
mapping results are:

| root/map | BA | OFF gain | opposite BA | registered mean conditional gain |
|---|---:|---:|---:|---:|
| root 0 / W+ | .578125 | .078125 | .421875 | .879937 |
| root 0 / W- | .515625 | .015625 | .484375 | 1.001103 |
| root 1 / W+ | .500000 | .015625 | .500000 | .664463 |
| root 1 / W- | .531250 | .015625 | .468750 | .570680 |

Every registered spill family fails the `.05` reported mean-TV bound, with
values from `.275157` to `.659671`. The score contradiction below means these
cannot presently be promoted as calibrated probability distances; they remain
the frozen reducer outputs.

The fixed `.5`-nat all-key optimization gate is itself impossible for 30 of
64 key/map cells from OFF headroom alone. Its failure must not be interpreted
as evidence against learning. Binding near chance in strict generation is a
separate valid negative observation. Score-derived spill and gain values are
provisional until the causal-score path is repaired.

## Causal-score contradiction found during the new reduction

For each saved score pair `(s0,s1)`, define

```text
L_ACT = log(exp(s0) + exp(s1)).
```

The two candidates purport to be complete native continuations
`ACT: -mem2reg\n`+EOS and `ACT: -gvn\n`+EOS. If the stored scores were valid
causal log likelihoods under the same prefix, `L_ACT(ON)-L_ACT(OFF)` would
measure total probability entering the two-action class without crediting
either member as correct. Applying it to the sealed records produces:

| adapter | own held | missing | unsupported | neighbour | wrong root |
|---|---:|---:|---:|---:|---:|
| root 0 / W+ | 25.581 | 28.972 | 27.737 | 27.743 | 25.325 |
| root 0 / W- | 25.603 | 28.968 | 27.773 | 27.748 | 25.333 |
| root 1 / W+ | 25.343 | 28.619 | 29.591 | 29.218 | 25.618 |
| root 1 / W- | 25.352 | 28.592 | 29.541 | 29.240 | 25.596 |

These are arithmetic transformations of the stored scores, **not validated
probability-mass gains**. The interpretation fails an elementary causal
check: `266/832` score requests, all ON, have
`exp(s0)+exp(s1)>1.000001`; the maximum is `1.3802383379`. Two distinct
complete LF+EOS continuations under one identical causal prefix cannot have
summed probability above one.

The builder's completed no-fit diagnosis localizes the inconsistency. For the
maximal contradictory prompt, the probability of the same two next tokens
changes according to which future suffix is appended:

```text
OFF candidate A forward: .991418 / .008577
OFF candidate B forward: .989008 / .010987
OFF prefix-only forward: .982007 / .017986

ON  candidate A forward: .705245 / .293990
ON  candidate B forward: .319712 / .676831
ON  prefix-only forward: .592001 / .406876
```

The maximum common-prefix log-probability disagreement is `1.2788` nats OFF
and `4.7599` nats ON. Recorded eager-attention masks do contain causal
`-inf`-equivalent future entries, so this is not literal future-token leakage.
The builder's follow-up localized the defect to sequence-shape sensitivity in
BF16 for this prompt:

```text
BF16, natural unequal lengths: summed mass 1.380238, inconsistent prefix
BF16, equal total shape:       summed mass 0.997894, exact prefix agreement
FP32, natural unequal lengths: summed mass 0.998979, max delta 7.06e-5
FP32, equal total shape:       summed mass 0.998970, exact agreement
```

Thus separately forwarding unequal-length candidates in BF16 did not supply
one coherent causal probability measure. This localization was one-prompt
evidence; the terminal complete rescore below supplies the all-request check.

Therefore neither this table nor the report's NLL/conditional-TV terminology
is valid probability evidence yet. The builder made a scoped, non-material
repair: pad both candidates to identical total length with future-only EOS
tokens, preserve the original scored-token mask, make positions explicit, and
fail closed unless the shared-prefix distributions agree and the disjoint
candidate mass is at most `1 + 1e-6`. Sixty-two CPU tests pass. This is an
internally coherent fixed-shape diagnostic because those invariants pass over
all `832` saved requests. It is not yet a canonical, generation-equivalent
likelihood: the motivating prompt's first branch probability was `.5920` at
the natural prefix shape, `.7052` under equal-shape BF16, and `.7289` under
equal-shape FP32. A shared-prefix/trie scorer, or a complete higher-precision
comparison showing decision invariance, is required before treating these as
model-intrinsic likelihood/NLL gates. The original report stays unchanged.

The supplementary no-fit rescore completed at `14:00:28 UTC` in `347.468`
seconds. It made zero fits, produced `832` replacement diagnostic scores, and
reused all `880` original generated outputs. Its terminal
`supplementary_report.json` SHA-256 is
`f066f98d19cd3801253d63b0cf0622b77865feabffddaf26c25baa96a32e18df`.
Independent raw enumeration finds exact equality in all `2,496` shared-prefix
token log probabilities and zero mass violations; the largest two-candidate
mass is `.9989317839`.

Under this fixed-shape diagnostic, mean conditional target gains are `1.079`,
`.951`, `.647`, and `.608` nats for root0/W+, root0/W-, root1/W+, and
root1/W-. These positive means coexist with many negative per-key gains and
generation near chance. Meanwhile the mean gain in total probability assigned
to the two registered native actions is about `25.93--26.69` nats in all four
cells and remains broad on missing, unsupported, neighbour, and wrong-root
prompts. Repaired binary spill means remain large (`.280--.656`). The
bounded diagnostic interpretation is therefore not selective mapping:
training strongly installed the native two-action response class, with incomplete
key-conditioned association and extensive off-target change. This cannot
promote the frozen run gates.

A fresh implementation/custody audit also finds that the supplementary runner
does not verify the original sealed inventory before consuming adapters and
generation records, nor seal a replayably state/hardware-bound supplementary
inventory. The builder's own external checks and this watcher's raw arithmetic
support debugging use, but paper-grade promotion requires those bindings and
corruption/wrong-state tests.

Training did optimize something real: mean target-token loss is
`.244--.267`; the last 32 training steps average `.094--.101`, and adapter
update norms are `1.789--1.886`. Those facts do not establish selective
mapping storage. Most supervised response tokens are common native-action
syntax, consistent with the repaired score evidence that common action-class
mass dominated conditional association.

## Exact-training-row localization

The prospectively frozen, no-fit exact-row diagnostic then evaluated all 128
actual training prefixes for each map and root, with target bytes withheld
from generation. Root 1 completed in attempt 1; root 0 attempt 1 stopped after
OFF because a 15-second `nvidia-smi` identity query timed out before the first
adapter load. That partial root was preserved, and one fresh full root-0
attempt completed unchanged. All six terminal state workers have
`owned_group_empty=true`, both controllers are absent, and the GPUs are free.

Terminal report identities are:

```text
root 0, attempt 2: 4b1be70a8e2b20a23a2d76b32fb7e02564a958545b7eb8afe870e32b7e832e69
root 1, attempt 1: 5b349b1b4742f061f0c884ef37b7c4f3478845d46b5f27424c97237d6d492fc2
```

Matching-map results are:

| adapter | exact-train generation | exact-train fixed-shape score choice | original held generation |
|---|---:|---:|---:|
| root0/W+ | .53125 | .46875 | .578125 |
| root0/W- | .53125 | .4921875 | .515625 |
| root1/W+ | .50000 | .4921875 | .50000 |
| root1/W- | .4921875 | .5234375 | .53125 |

Every generation remains syntactically valid, but none of the four adapters
recovers its balanced conditional mapping even on the exact training forms.
The action distributions instead show coarse global bias: root0/W+ emits
action 0 on 104/128 prompts, root0/W- emits action 1 on 124/128, root1/W+
emits action 1 on 128/128, and root1/W- emits action 0 on 113/128. Direction
varies across cells; the invariant is failure to condition on the key. This
rules out the hopeful “stored association, held paraphrase extraction failed”
explanation for these four instances. The writer learned action syntax/global
preference rather than a usable key-to-action relation.

The highest-information next fit is therefore one controlled objective test,
not another broad heat/rank sweep: keep the exact four corpora, clean bases,
maps, dose, and evaluation, but supervise or contrast the action-specific
branch after the already-correct common `ACT:` prefix. The base already has
100% valid syntax, so rewarding shared syntax and EOS is unnecessary and
empirically dominant. A target-suffix loss arm is the minimal implementation;
a pairwise correct-versus-incorrect continuation objective is the stronger
fallback if that arm still collapses globally. Any new fit must retain the
same held, exact-row, interface, and locality endpoints and be bound before
outputs.

## Highest-information next measurement

The exact-row generation above has already separated the main cases:

1. **stored but not extracted across renderings** is contradicted here because
   exact-train generation is also near chance;
2. **usable conditional mapping not stored** is supported for these four
   instances; and
3. **broad action-class change without selectivity** is supported by the
   global action collapses and fixed-shape diagnostic, subject to the latter's
   stated backend/custody limits.

The exact-train panel keeps strict generation separate from fixed-shape score
choice and cannot repair or promote this run. It has served its localization
purpose; repeating the unchanged writer is lower information than changing
the differentiating-target objective under the same controls.

## Claim boundary

This diagnostic establishes neither authentic experiential learning nor a
general limitation of LoRA. It establishes that this exact rank-8,
token-mean-SFT, 128-row/two-epoch recipe failed held-form conditional
generation on four supervised root/map instances, and that its score path is
invalid under unequal-shape BF16 evaluation. The supplementary equal-shape
rescore is internally consistent and strongly suggests broad native-action-
class change, but it is a shape-conditioned diagnostic with incomplete
custody—not a canonical likelihood assay. It does **not** qualify the writer
or establish conditional exact-row storage. Exact-train generation now shows
that usable exact-form association is absent in all four fitted instances;
this is a recipe failure, not a general limitation of LoRA or experiential
learning.
