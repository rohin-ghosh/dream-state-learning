# R106 composition — MATH764 minimal-default FULL / masked / BASE

Main's CPU-only reduction completed **2026-09-15 06:40:47 UTC**, using the
existing 64 matched held outputs per arm. No model calls, fits, parent calls,
accuracy rescoring, generator changes or training admission. Exact native
content token IDs matched tokenizer re-encoding for all **192/192** outputs.

## Main conclusion: branches exist, mostly terminal checks in this review

The former method-count-based **“no branching” claim is withdrawn as an R106
claim**. Main read the first four complete outputs per arm, then all eleven
outputs flagged by the lexical check/aside screen. The second sample is
deliberately marker-selected; its positive fraction is NOT a population rate.

| Author-reviewed evidence | FULL | Masked OFF | Untrained BASE |
|---|---:|---:|---:|
| Whole-cohort mean generated tokens, including EOS |186|246.046875|235.59375|
| Fixed first4 outputs: departure/return present |0/4|0/4|0/4|
| Additional marker-selected outputs reviewed |5|2|4|
| Confirmed outputs with any departure/return, **lower bound of 64** |5|2|4|
| With return to intermediate computation, **lower bound of 64** |1|0|2|
| With return to final answer, **lower bound of 64** |5|2|4|
| Remaining semantically unreviewed outputs |55|58|56|

Mid-solution and terminal categories overlap for outputs containing both.
**Terminal checks do not enter the mid-solution count.** All 23 reviewed
outputs have one main worked solution method under the separately retained
method definition; verification is not automatically a second solution method.
These lower bounds do not establish a FULL advantage or useful learned branching.

Concrete author findings, bound by native call and text hashes in `COMPACT.json`:

- FULL positions17,47,51 verify a solved value against other quantities, then
  return to the answer. These are actual checks, not a second worked method.
- FULL56 also checks, but falsely says 26 is double11: branching shape **with
  an erroneous check**, not useful verification. Do not erase it from shape
  counts or relabel it correct.
- FULL27 questions the triangle premise, resumes calculation with a different
  angle total, then calls its zero-angle result impossible but emits it anyway.
  This has a mid-line departure and a later judgment, with inconsistent resolution.
- BASE27 similarly questions the premise. BASE56 re-evaluates a negative result,
  returns to the setup, and loops through repetitive premise judgments before
  an inconsistent final answer. These are not FULL-installed capabilities.

## Composition, author-reviewed fixed sample

Shares below are percentages of generated **content tokens**, not words;
EOS is excluded. The entire segment is assigned its dominant function;
necessary main-line planning, connective prose and mathematical rendering are
included in direct computation. This coarse segmentation is **not** an exact
clause-level linguistic partition. Mixed sentences can contain restated givens
inside a direct-computation segment. First4/arm is fixed, nonrandom and small.

| Token share (%) | FULL,675 tokens | OFF,1020 tokens | BASE,929 tokens |
|---|---:|---:|---:|
| Direct computation, main-line explanation and scaffolding |92.889|89.020|90.743|
| Restated givens |2.370|3.725|4.736|
| Checks / verification |0|0|0|
| Judgments / asides |0|0|0|
| Meta-comments |0|0|0|
| Final answer, including natural-language conclusion |4.741|7.255|4.521|

Within these four matched problems, FULL is more compact, while the visible
work remains the ordinary problem decomposition and arithmetic. This supports
a limited description of **compression of main-line exposition**, not a claim
about where every token in the full population went or the mechanism of errors.

## Whole-cohort automated composition — explicitly a lexical proxy

| Proxy token share (%) | FULL,11840 content tokens | OFF,15683 | BASE,15014 |
|---|---:|---:|---:|
| Direct-computation fallback, including scaffold/unrecognized functions |94.003|94.006|93.007|
| Restated givens |1.664|2.774|3.290|
| Checks / verification |1.115|0.408|0.426|
| Judgments / asides |0.363|0|0.626|
| Meta-comments |0|0|0|
| Final markers / boxed answer |2.855|2.812|2.651|

**Do not interpret these as semantic population shares.** A check marker often
labels only its introductory sentence, missing the following verification
arithmetic. Main's targeted audit also found43 BASE meta-comment tokens where
the proxy returned zero. The proxy is useful for finding evidence to read, not
certifying absence. `COMPACT.json` retains both proxies and author counts,
with sample labels, rather than silently replacing one with the other.

## Independent Fable audit — different taxonomy and scope

Origin commit `42a98cc08c5eccdd17d6c5ef3db8302436ee910b` contains Fable's notebook
entry labelled06:45Z. It reports320 classified outputs across five cohorts and
32 paired minimal-default tasks at positions16–47: same computational steps
FULL versus BASE on28/32, pure compression on17/32. It reports scaffold **word**
shares BASE0.35/OFF0.30/FULL0.20 and display LaTeX63/64,62/64,35/64, respectively.
Those are attributed independent results, not Main's token-based remeasurement;
Fable separates scaffolding whereas Main's six-class taxonomy includes it in
direct computation. Their percentages are therefore not interchangeable.

Fable reports eight FULL excursions versus seven BASE and two OFF in the full
minimal cohorts. Main's smaller, selected audit supplies positive lower bounds,
not a contradiction or an exact recount. Fable's no-added-checks observation is
bounded to positions16–47; Main's additional FULL51/56 checks are outside that
paired window. Prompted FULL's reported46 terminal Check blocks must remain
separate from minimal-default behavior and from **mid-line** excursions.

The paired examples suggest compression can accompany errors. They do not
identify the cause of the complete prompted54/64 versus59/64 accuracy gap, nor
prove that underlying reasoning was undamaged. No accuracy-driven parenting
intervention or claim promotion follows.

## Reproduction and provenance

- Native report: A100 `/localhome/local-rohing/R106_COMPOSITION_SPLIT_20260915.json`,
  SHA256 `82bd121655483ced587c3adac6b31d283fcb3a5af2a15bcad37df5ea9719b90f`.
- Native author labels: `/localhome/local-rohing/R106_AUTHOR_SPLIT_20260915.json`,
  SHA256 `5257dbba4a82c6cff70d992ac5683815216f82be7e18a959e8db15b439585a1f`.
- Reducer source SHA256 `cf92ac05a77294fb047364a28cf7be7e47a848a10353710afff0f0be212b9715`.
- Author-label source SHA256 `a459c87891ae5b0da55c939e5b54395a385856c5e9a77f77389ce571dada063a`.
- `COMPACT.json` drops only segment-boundary arrays from the native report;
  no raw outputs are copied to the VM/repo. Original source calls remain native.
- Main10 composition tests plus2 notebook-integrity tests PASS. Full native
  validation checks all annotations, token conservation and matched task sets.

Future META_STEERED generator design: encourage noticing/judging **while**
working and returning to the computation; retain an unhinted exhaustion arm.
It remains a labelled prospective arm, not an unlogged prompt replacement.
