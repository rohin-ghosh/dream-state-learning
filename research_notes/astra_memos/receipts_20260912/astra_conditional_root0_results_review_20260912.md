# Conditional root0 — terminal results review

**2026-09-12 — EDITSTOP receipt.** Technical completion is supported; scientific
qualification is narrower. Both adapters express their assigned conditional
maps exactly on the registered panels, but locality fails, and REVISE's
intended-comparison interpretation remains **UNQUALIFIED** by the public-ID
shortcut. No L1/Q0/H1 verdict, promotion, freeze, retry, or run intervention.

## Evidence and reviewer scope

Read only the authorized local terminal extraction and
`/tmp/astra_conditional_root0_independent_analysis_clockfix_20260912.json`.
Rehashed **all 1,801 bound files**, checked all **672 raw generation texts**
against the analysis, independently rederived exact train/dev targets from
public prompt fields, and resummed all **576 complete-candidate likelihoods**
from the 192 raw scoring receipts. All matched. Every signed pair interaction
and both endpoint log odds also matched. The analysis reports **six COMPLETE
phases, six raw/reduction MATCHes, summary MATCH, and no issues**.

Analysis JSON SHA256:
`88053fd1ab0e6a7c6ef9e225a981f273b83ba0e799272b9f30c668286c31ff14`.
Its bound clock-fixed analyzer SHA256:
`fbc6394b36fbce270763137620f7dac7c0c1b2cb2131513d0a9ddef4ebfa7e70`.
I authored the original independent analyzer and shortcut recount, **not the
run or corpus**. This is therefore not a fresh-author review of my own analyzer.
Only this review file was written; no repository/network/Git/GPU/native work,
model/tokenizer imports, or duplicate formation preparation.

## Exact generation endpoints

Entries below are **AUTH-target / DERANGED-target correct counts**. Each count
is identical for semantic joint and strict joint; individual target-component
counts also equal the corresponding joint count. Train denominators are
**64 per operation**; dev denominators are **32 per operation**.

| State | Train PROSPECT | Train REVISE | Dev PROSPECT | Dev REVISE | Strict syntax, each operation: train; dev |
|---|---:|---:|---:|---:|---:|
| OFF | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0/64; 0/32 |
| AUTH | 64 / 0 | 64 / 0 | 32 / 0 | 32 / 0 | 64/64; 32/32 |
| DERANGED | 0 / 64 | 0 / 64 | 0 / 32 | 0 / 32 | 64/64; 32/32 |

Generation twins: for **each** PROSPECT belief/goal and REVISE outcome/prior-
action family, OFF passes **0/32 train, 0/16 dev**, on either map. AUTH passes
**32/32 train, 16/16 dev** on AUTH and zero on DERANGED; DERANGED passes those
same complete counts on DERANGED and zero on AUTH. Semantic and strict twin
passes agree. These are paired endpoints, not extra independent observations.
Each state has 128 train + 64 dev + 32 control calls, with no missing rows.

## Complete-candidate signed likelihood endpoints

For each map fix `A=target(x0)`, `B=target(x1)`. Define
`d0=L(A|x0)-L(B|x0)`, `d1=L(A|x1)-L(B|x1)`, and `I=d0-d1`.
All entries are means over the **same 16 registered twins**, in nats, rounded
to six decimals; the authorized JSON retains every full-precision endpoint.
“Both own” counts pairs with `d0>0` **and** `d1<0`, not merely positive I.

| State | Operation | Map | Mean d0 | Mean d1 | Mean I | Both own /16 |
|---|---|---|---:|---:|---:|---:|
| OFF | PROSPECT | AUTH | 4.529014 | -5.766438 | 10.295452 | 11 |
| OFF | PROSPECT | DERANGED | 9.252937 | -9.547448 | 18.800385 | 13 |
| AUTH | PROSPECT | AUTH | 9.995983 | -10.434769 | 20.430752 | 13 |
| AUTH | PROSPECT | DERANGED | 5.922405 | -5.710034 | 11.632438 | 8 |
| DERANGED | PROSPECT | AUTH | 4.474740 | -4.030888 | 8.505629 | 9 |
| DERANGED | PROSPECT | DERANGED | 18.820038 | -18.957576 | 37.777614 | 16 |
| OFF | REVISE | AUTH | -8.896033 | -9.124001 | 0.227968 | 1 |
| OFF | REVISE | DERANGED | 8.896033 | 9.124001 | -0.227968 | 0 |
| AUTH | REVISE | AUTH | 7.891964 | -8.154373 | 16.046338 | 16 |
| AUTH | REVISE | DERANGED | -7.891964 | 8.154373 | -16.046338 | 0 |
| DERANGED | REVISE | AUTH | -2.817219 | 5.513384 | -8.330603 | 0 |
| DERANGED | REVISE | DERANGED | 2.817219 | -5.513384 | 8.330603 | 14 |

PROSPECT uses **four distinct fixed-map candidates**, REVISE two genuinely
swapped candidates. The latter's map effects are exact negatives, **not
independent replications**. PROSPECT's two maps likewise do not double the
16-twin denominator. Shared OFF is counted once. PROSPECT assigned-map mean-I
changes from OFF are **+10.135300 AUTH** and **+18.977229 DERANGED**; positive
OFF contrasts already show input-dependent likelihood sensitivity, despite
zero strict generated panel answers. Positive mean I neither guarantees every
endpoint preference nor establishes newly acquired general ability.

These are sums of stored token-logprob scalars for complete continuations,
including the stored EOS position, without length normalization. **No logits,
native tokenization/EOS identity, token decoding, or forwards were independently
recomputed.** Raw scalar/text correctness remains capture-dependent.

## Locality and caps

All control denominators are **16 executions per family per state**.

| State | Family | Valid | Correct | Exact | Tag spill |
|---|---|---:|---:|---:|---:|
| OFF | Addition | 16 | 16 | 16 | 0 |
| AUTH | Addition | 8 | 8 | 3 | 13 |
| DERANGED | Addition | 16 | 16 | 0 | 16 |
| OFF | Copy | 12 | 14 | 14 | 0 |
| AUTH | Copy | 0 | 0 | 0 | 16 |
| DERANGED | Copy | 0 | 0 | 0 | 16 |

Copy has **eight unique prompts**, each executed twice: unique-all-correct is
**7/8 OFF, 0/8 AUTH, 0/8 DERANGED**. Frozen copy validity excludes internal
hyphens, so validity can be lower than exact correctness; this is not silently
repaired. With 16 controls, the .05-loss allowance permits **zero lost counts**;
spill maximum is **0/16**. Both adapters violate locality. DERANGED retains
addition valid/correct 16/16 but loses every exact response and spills on all
16—numeric correctness alone does not rescue interface retention.

The 672 generations returned **18,848 tokens / 43,008 ceiling**; observed
per-call maxima are **64 OFF, 15 AUTH, 16 DERANGED**, against cap 64. Across
864 calls, maximum measured call duration is **13.125738s / 120s**. Worker
allowance is 600s; largest measured worker reservation is **477.098527s**.

Measured nested windows, seconds: generation calls **624.098770** + scoring
calls **41.925535** = **666.024305**, within worker reservations **1215.807358**,
within controller **1527.156751 / 4500**. Release observation is at
**1580.776011** after launch; completed collection at **1582.983845**. Collection
itself is **26.751393 / 300**. Add prior-fit reservation **464.397178** once:
**2047.381022519 / 5400** total. Do **not** add nested worker/controller/call
windows again. Input-token accounting is 46,581 generation + 49,344 scoring =
**95,925**; scoring has **8,544 target tokens, 49,440 padded forward tokens,
576 candidate forwards**. Scored tokens are not generated output tokens.
Release evidence is historical, not a new/current GPU-vacancy check.

## Timing repair and interpretation

Main's quoted collector sum `2047.381022453308` differs from
`464.397178 + 1582.9838445186615 = 2047.3810225186614` by
**6.535333341162186e-8 seconds**. This exceeds 1e-8 but is below 1e-6, consistent
with floating-point cancellation in epoch-derived arithmetic. The described
**derived-timestamp-sum-only 1e-6** repair is numerically appropriate; no
scientific tolerance relaxation is needed. **Scope limitation:** no patched
source/test diff exists in the authorized inputs, so I could not byte-review
the actual diff. Scientific tolerance remaining **1e-8**, **54 tests PASS**,
and preservation of the first PARTIAL output are Main-reported, not freshly
verified here. The corrected evidence's arithmetic and bindings are verified.

REVISE is **UNQUALIFIED as evidence of using literal EXPECTED**: the prior
frozen-corpus recount demonstrated a train-only `(square suffix, OBSERVED,
PRIOR)` lookup scoring **64/64 train, 32/32 dev on both maps**, including both
twin families, while ignoring EXPECTED. Today's positive results cannot
distinguish that shortcut from intended comparison; they do not establish
which mechanism the model used. PROSPECT's corresponding omitted-factor
ID projections have .50 joint ceilings, so this specific defect does not
transfer to it; its conditional controllability evidence remains separate.

**Retention failure does not erase latent ability.** It establishes harmful
adapter-on behavior on these controls, not destruction of all base competence.
OFF's control performance and PROSPECT likelihood sensitivity coexist with
adapter-induced exact conditional behavior and severe spill. No composition,
Q0, H1, or full L1 conclusion follows.

**Narrow next decision:** classify root0 as registered map controllability
with locality failure, leaving REVISE mechanism unqualified; require a
prospectively EXPECTED-crossed diagnostic before upgrading that interpretation.
Do not repeat the same confounded panel to resolve it. Main's native formation
preparation remains Main-owned; no new code, duplicate preparation, freeze,
or additional run is requested by this receipt. **EDITSTOP.**
