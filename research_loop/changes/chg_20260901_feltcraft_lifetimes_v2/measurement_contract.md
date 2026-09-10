# FeltCraft-Lifetimes CPU measurement contract v2

**Status:** proposal only; controls the exact finite CPU gate.

## 1. Finite conditional measure

The posterior universe contains every registered typed alignment, family
alignment, twin transform, descriptor attachment, and target calibration
consistent with `world_contract.md`. Because no world or target is rejected,
`A=1` is constant. Code must nevertheless compute and report both
`p(d|x,e)` and `p(d|x,e,A=1)` and verify equality exactly.

All probabilities are exact rationals. A target-local quotient is permitted
only after exhaustive equality with the full product on the bound golden
worlds. Monte Carlo posterior estimates are forbidden in CPU v2.

A positive relation is publicly identified at cut `c` iff its posterior under
the unconditional generator family, given only the legal public source prefix,
is exactly one. `N_unique_public_edges` counts deduplicated identified local
relations. Repetitions, paraphrases, compiler views, target selection, and
future evaluation add zero.

## 2. Exact deterministic controllers

All controllers maximize success probability, then minimize expected action
count, then choose the lexicographically smallest canonical action bytes. They
use no RNG. The exact search cap is `2^24` hypothesis-state-action expansions
and 1 GiB per target. Exceeding either invalidates the instrument item rather
than scoring a behavioral zero.

- `BF`: target-visible bytes and within-target observations; canonical
  grammar-valid trials; no generator prior or lifetime.
- `NPLUS`: `BF` plus the complete frozen generator/selection specification and
  the regime label as an audit-only advantage; no source prefix.
- `ATOM`: `NPLUS` plus source-identified handle-local atoms and S calibration
  atoms; all cross-instance alignment statistics deleted.
- `SCHEMA`: `ATOM` plus the exact pretarget cross-instance descriptor-alignment
  sufficient statistic; no target outcome or hidden binding.
- `SOURCE`: target-visible bytes plus complete legal public source prefix and
  generator specification. This is the legal-history ceiling, not an oracle.
- `ORACLE`: full target-relevant hidden state; scorer only.

Input schemas and taints are closed per controller. CPU controllers receive
typed sufficient statistics once at target start and make no model/memory
queries. Future bounded-reader/model comparisons require another contract.

## 3. Per-target hard gates

Every one of the 24,576 registered target cells
`128 seeds * 2 twins * 2 regimes * 4 cuts * 12 targets` must satisfy its
applicable gate; pooling cannot rescue a failure.

- `ORACLE=1` with a serialized replayable shortest plan.
- `SOURCE=1` for every A2, A3, and MOTIF-S target.
- `NPLUS<=.35`, `BF<=.35`, and every static leakage projection `<=.35`.
- `ATOM<=.35` on all S targets.
- MOTIF-S decisive posterior is a point mass and `SCHEMA=1`.
- RANDOM-S decisive maximum posterior and `SOURCE` value are exactly 1/4.
- In RANDOM-S,
  `I(decisive; other_instance_descriptors | target, calibration, A)=0`
  as exact rational equality.

For exact CPU S controllers, the registered gain is:

```text
G_MOTIF = SCHEMA - ATOM = 3/4
G_RANDOM = SCHEMA - ATOM = 0
I_schema = G_MOTIF - G_RANDOM = 3/4
```

These exact values are instrument certificates, not learned-system results.

## 4. Leakage projections

For each target enumerate the accepted-measure optimal action value under:

- target-visible bytes;
- state fields only;
- identifier bytes and ordering only;
- descriptor bytes and positions only;
- source action/outcome marginal frequencies without semantic pairings;
- passive structure: field presence/order, UTF-8 lengths, candidates, budgets,
  event counts/times, and marginals;
- selection-only information (`A=1` and publicly inferable matching facts).

Each value must be at most .35 per target. A self-test independently injects
the decisive action into each projection and must recover value 1. Probe
results never select or replace targets.

## 5. Prefix-free descriptive codecs

CPU v2 reports oracle code lengths but cannot earn a compression claim.

Primitives:

- `G(n)`: Elias-gamma code of nonnegative `n+1`;
- `F_K(x)`: `ceil(log2 K)` bits for `0<=x<K`; unused words invalid;
- `BYTES(s) = G(len(s)) || s`;
- sequence: `G(count)` then self-delimiting elements.

Both `L_enum` and `L_schema` start with `BYTES` of the exact hash-bound decoder
source, a 256-bit public-side-information hash, and a two-bit model-class tag.
Public side information may include handle/descriptor catalogs and deck IDs,
but no recipe, role, alignment, target answer, or answer-bearing provenance.

`L_enum` encodes every identified local binding independently: count, family,
instance, relation tag, output/ingredient/site indices, sorted delta-coded
public provenance roots, and zero numeric-parameter flag.

`L_schema` literally encodes the eight-role/four-edge template, not a free ID;
one model-selection bit; for every family either independent instance
permutations or one persistent permutation plus a deviation bit-vector and
full deviation permutations; explicit exception count including zero; the
same provenance obligations; and zero numeric-parameter flag. Permutations use
Lehmer rank in `F_96`. Adding another schema family requires a new reviewed
code.

Required tests: round-trip, malformed-word rejection, prefix-freeness,
serialization-order invariance, and hand-computed golden lengths.

## 6. Matched loss

A scorer-only deck frozen before generation contains every decisive relation
query plus an equal number of namespace-sampled nontarget local relations per
family. For each decoded representation report:

- edge loss: incorrect or abstained relation answers / all queries;
- action loss: `1-success` of the same exact controller;
- active bytes: encoded bytes plus index/working high-water bytes;
- retained audit/provenance bytes separately and jointly.

Matched loss requires, in every cut/regime/stratum:

```text
edge_loss_schema <= edge_loss_enum + .01
action_loss_schema <= action_loss_enum + .02
```

A future compression claim additionally needs prospective learned action gain,
strict `L_schema<L_enum`, and strict active-byte reduction at every registered
growing post-native cut. Decoder/template/model-selection/provenance cost is
never free.

## 7. CPU verdict

Precedence:

1. `REWORK`: nondeterminism, malformed serialization, posterior quotient
   mismatch, controller/codec bug, resource-cap overflow, missing receipt, or
   suffix/isolation failure.
2. `REJECT`: mechanically valid but any per-target coupling, solvability,
   leakage, RANDOM independence, MOTIF identification, twin, or growth gate
   fails.
3. `RETAIN`: every hard gate passes. MDL ordering is descriptive and cannot
   change this verdict.

The receipt reports every target and cut separately, then equal-weight means
within twin and super-seed. It cannot promote itself to a model gate.
