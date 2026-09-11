# Multi-key writer gateway V10R1 — ratification candidate

Status: proposal only. No implementation or execution authority.

The effective contract is V9 exact scope (SHA-256
`eac3e25c93230f3788612b3d0a25c0dac3609d49b4a5d9e28cf853ba806c0955`),
then V10 exact scope (SHA-256
`12a077950730c3abaef32b04a861d901ef4bae25a22e640b152472f5f364f549`),
then this V10R1 amendment. Later text controls a conflict. V10R1 makes the
V10 choices below explicit and applies the two corrections required by the
V10 consensus (SHA-256
`147aebaaf0b974a37897acc724c6fe27c8e82c6f94db0c1e775eba3d57a1ce7e`).
Every unmodified V9/V10 term remains normative.

## Deliberate byte rules

The line-anchored, exact-case `ACT:` occurrence rule in V10 is deliberately
selected instead of anywhere-substring counting. The ASCII-only boundary rule
is deliberately selected instead of Unicode whitespace stripping and applies
to both primary binary validity and unrelated native-interface equality.
There is no Unicode normalization. In particular, an otherwise exact output
wrapped in valid UTF-8 U+00A0 bytes is invalid for primary scoring and
incorrect for native-interface scoring. The golden table must include those
two U+00A0 negative cases.

Multiple-ACT rate is computed and reported for every root-condition pair over
its fixed 64 primary outputs. Only the four adapter conditions are
gate-bearing: each adapter must have zero multiple-ACT outputs. OFF
multiple-ACT rate is diagnostic-only and cannot change `interface_ok` or the
final label. A complete fixture in which only OFF has `multiple_ACT=true`
must preserve the otherwise applicable label; the paired adapter-only fixture
must produce `INTERFACE_INVALID` at V9's inherited precedence.

## Exact maximum pass wording

The maximum permitted pass statement is:

> Across two engineered roots, in each of four root-map adapters, all 16
> evaluated tool-by-mode keys met the predeclared per-key median action-choice
> NLL-gain threshold. Each adapter met the aggregate and per-stratum generated
> behavior gates and the directional-margin gate on at least 12/16 keys and
> 6/8 keys per stratum. On each frozen scored multiset, maximum target balanced
> accuracy was exactly 1/2 for each of the constant, tool-only, mode-only,
> stratum-only, and stratum-by-mode deterministic policy families, and for
> every declared non-key categorical surface-covariate predictor both alone
> and crossed with mode; therefore passing adapter behavior was not solely any
> such enumerated policy on the evaluated surface. No change beyond the
> predeclared spill or native-interface bounds was detected.

This is a supervised seen-key writer-capacity statement. It is not a fitted
shortcut-probe result, an internal-mechanism result, sixteen independent
memories, directional success on every key, child authorship, lived learning,
DREAM, retention, parenting, generalization, connected memory, recurrence,
continual learning, or a whole-organism result.

## Boundary

The implementation request remains exactly one experiment module, one focused
CPU test file, one thin launcher, deterministic CPU receipts, and two local
reviews. No real tokenizer, model, training, adapter, benchmark, GPU, resource,
lineage, parenting, scientific-claim, release, submission, or C11 action is
authorized. Full guard completion and enforcement remain deferred to the
final paper-grade C11 run.
