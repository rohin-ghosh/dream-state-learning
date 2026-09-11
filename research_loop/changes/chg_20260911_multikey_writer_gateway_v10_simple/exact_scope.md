# Multi-key writer gateway V10 — final local amendment

Status: proposal only. No implementation or execution authority.

V10 incorporates the complete normative V9 scope at
`research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md`
(SHA-256 `eac3e25c93230f3788612b3d0a25c0dac3609d49b4a5d9e28cf853ba806c0955`)
and changes only the definitions below. The V9 consensus requiring this
rework is incorporated at SHA-256
`cd3e243b01e439ce2facb19ed745ee265572e75d7785eeb35fc1efdbb2977158`.
If this amendment conflicts with V9, this amendment controls. Every V9 term
not changed here remains normative.

## 1. Key-level directional margin

For each key and adapter, the key-level directional margin is the median of
that key's four held-template values of
`ell_target - ell_opposite`. For four values, median is the arithmetic mean of
the second and third values after ascending numeric sort. The 12/16 overall
and 6/8-per-stratum requirements apply separately to every one of the four
root-map adapters.

## 2. Multiple-ACT predicate

The request layer preserves the complete decoded model-output UTF-8 bytes.
For the separate multiple-ACT diagnostic, a protocol-line occurrence is an
`ACT:` byte sequence that is either at byte offset zero or immediately after
LF (`0x0a`), after skipping zero or more ASCII space or tab bytes, with exact
case. The remainder of that line may be arbitrary. An output is
`multiple_ACT=true` exactly when it contains at least two such occurrences.

This diagnostic does not make an output valid. Primary binary validity still
requires the complete output, after removing only ASCII space, tab, CR, and
LF bytes from both outer boundaries, to equal exactly `ACT: a0` or
`ACT: a1`. Every other output is invalid and incorrect. Multiple-ACT rate is
the count of `multiple_ACT=true` primary outputs divided by the fixed 64
primary items for that root and condition; the required rate is exactly zero.

Golden cases include: one valid line; two valid ACT lines; one valid and one
malformed ACT line; indented ACT lines; inline `ACT:` not at a line start;
lowercase `act:`; repeated substrings on one line; leading/trailing boundary
whitespace; and extra prose.

## 3. Unrelated native-interface scoring

Each of the eight frozen unrelated prompts has one manifest-bound expected
single-line UTF-8 byte string of the form `ACT: <native_action>`, where the
native action is neither `a0` nor `a1`. A native-interface output is correct
exactly when its complete output, after removing only ASCII space, tab, CR,
and LF bytes from both outer boundaries, equals the expected byte string.
Case, internal whitespace, spelling, punctuation, or any extra internal text
must match exactly; there is no repair, first-line selection, or binary-action
parser reuse. Missing or truncated model output follows V9's evidence rules.

`interface_ok` requires 8/8 correct for OFF and separately 8/8 for every one
of the four root-map adapters, in addition to V9's primary validity and
multiple-ACT requirements. Golden cases cover exact match, each single-field
mismatch, leading/trailing boundary whitespace, extra line/prose, casing,
missing output, and malformed native ACT text.

## 4. Maximum permitted pass wording

Replace V9's strongest pass summary with exactly this scientific scope:

> Across two engineered roots, in each of four root-map adapters, all 16
> evaluated tool-by-mode keys met the predeclared per-key median action-choice
> NLL-gain threshold. Each adapter met the aggregate and per-stratum generated
> behavior gates and the directional-margin gate on at least 12/16 keys and
> 6/8 keys per stratum. On the frozen target geometry, each named one-factor
> and declared surface-covariate policy family had maximum target balanced
> accuracy 1/2, so passing behavior cannot be solely one of those policies.
> No change beyond the predeclared spill or native-interface bounds was
> detected.

This describes deterministic target geometry and aggregate behavioral gates,
not fitted shortcut probes, sixteen independent memories, success on every
key's directional margin, an internal representation, or any broader learning
claim. All exclusions and the C11 deferral in V9 remain in force.
