# Fresh source-readiness audit: TWO-SLEEP-JUNCTION-v3

**Date:** 2026-09-13 PT

**Role:** fresh adversarial source-readiness reviewer

**Object:** commit `ac1feacb08581adf60972adc14eabd501c13847b`, file
`research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v3.md`,
verified SHA-256
`fafbd7818f607e0227328b13b47068f9d1493e244a297fc3c7e18bd882b61ad9`.

**Basis:** the v2 fresh audit, SHA-256
`c6b1575a82df99557848ea42f5ecd9f4171153f5c61e5ed960f119fc76d55b55`,
and the M-COMBINE-v2 dependency as it existed at the audited commit. This was
a repository/documentation audit only. I did not edit scientific source,
materialize a root, invoke a tokenizer/model, train, mount an adapter, inspect
a worker, or use a GPU.

## Verdict

**REWORK before CPU source authoring. `GO_CPU_SOURCE = FALSE`. All scientific
preparation/execution and claim gates remain false.**

V3 closes most of the large v2 gaps and is close to a source contract. The
upstream dependency is now genuinely content-bound; response forks are legal
and coherent; S2 ancestry is honest; INLINE versus ACTIVE is well defined;
RAW is serialized as two real calls with a fail-closed witness rule; and the
68-rollout call/token arithmetic recomputes. Four remaining contradictions
would still force a source author to choose scientific bytes or silently
violate a coupling/gate. They require a documentation successor, not a larger
experiment.

## P0.1--P0.6 disposition

| v2 blocker | v3 result | reason |
|---|---|---|
| P0.1 upstream BIRTH freeze | **PASS for CPU source** | The exact path, commit `654b54dc`, and SHA-256 `dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74` reproduce. The later receipt fail-closes checkpoint/tape/panel/runtime identities. |
| P0.2 unified phase/truth ledger | **REWORK** | One canonical phase ledger now exists, but its gate labels conflict with Section 8 and its reduced preservation panel has no executable threshold. |
| P0.3 coherent forks and ancestry | **PASS locally** | The earliest affected legal READ switches all future reads to one coherent transformed registry. S2 exact-S1 sharing is correctly restricted to AUTH/N/OLD_FILLER. |
| P0.4 literal seeds/wire/training/decode/active text | **REWORK** | Most pins are exact, but ATOM filler assignment, treatment-coupled batch order, parser grammar, invalid sentinels, seed encoding, and one reserved-domain size remain implementation choices. |
| P0.5 RAW serialization/witness | **PASS as data law; authorization REWORK** | R0--R15 now have exact role/message/mask composition and RAW_UNSAT stops the whole version, but no authorized stage can create the real-tokenizer witness required to open materialization. |
| P0.6 hard caps | **Arithmetic PASS conditional on the ledger** | `3,230` calls and `572,096` generated tokens/world, updates and presentations all recompute. The cap must be regenerated after the ledger repairs below, and the FLOP quantity needs an exact parameter-count meaning. |

## Exact remaining blockers

### P0.A — Treatment-dependent row hashes break exact causal-twin coupling

Section 4 orders every memory tape by
`(repeat, view, SHA256(canonical_row))`. O/T/N transforms change canonical row
bytes, and filler replacement changes them entirely. Their SHA ordering can
therefore differ from AUTH. This contradicts the promise that causal twins at
the same ancestry node share the presentation/unit-slot and RNG schedule; it
also defeats the exact slot match required for AUTH versus OLD_FILLER.
Identical starting RNG is not paired dropout when different examples occupy
the draws.

Bind one treatment-invariant semantic slot key before transformation (for
example, the authentic role/slot ordinal), order every arm on that key, and
record per-slot before/after hashes. RAW may keep its separately solved slot
assignment. Do not repair this in source by choosing whichever interpretation
is convenient.

### P0.B — The filler inventory does not define the ATOM tapes

V3 creates four `2E+1L` and two `2E+2L` blocks/world, then says the cuts use
the first S1 block, “atom-only uses the second/third LINK fillers,” and
OLD_FILLER uses the first S2 block. S1 ATOM must replace four LINK units and
S2 ATOM must replace six. The document does not state whether two filler rows
are duplicated, which filler occupies each authentic slot, whether the fourth
S1/second S2 block is used, or how their IDs/parents remain requestable under
the ATOM registry. Different choices produce different targets and gradients.

Enumerate the exact filler role-key inventory and a total map from each of the
four/six authentic LINK slots to one synthetic row, including reuse policy,
addresses, parents, provenance handles, target-slot key, and before/after hash.
Also spell out the already-named IL0/IL1 island edges rather than relying on a
reader to recover them from superseded prose.

### P0.C — The sole phase ledger and truth predicates disagree

P10/P50 label `ATOM_TEXT <=1/2` as **diagnostic**, while Section 8 states ATOM
must be `<=1/2` in each world and Section 11 opens S1/S2 on every row labeled
gate. The earlier closure required the zero-fit atom condition to establish
that the public interface actually needs LINKs before native fitting. Under
the ledger-as-sole-source rule, a 2/2 atom-text actor does not stop fitting;
under Section 8 it appears to fail the conjunction. Pick one prospectively.

The controller-preservation predicate is also incomplete. V3 reduces each
upstream 8-pair skill panel to four pairs at ordinals `0,2,4,6`, but Section 9
only says “meet upstream minima.” The upstream minimum is `>=6/8` and cannot be
applied literally to a four-pair subset. V2's proposed `>=3/4` plus absolute
and no-more-than-one-drop thresholds are not imported here. Bind every reduced
metric denominator, threshold, baseline comparison, and alias rule directly
in the canonical ledger.

### P0.D — The tokenizer witness is authorization-deadlocked

The status and Section 11 permit only dummy-ID/fake-tokenizer CPU work and
forbid scientific-root materialization and the real tokenizer. The same
section requires a tokenizer-bound RAW witness, identifier token checks, and
leakage/disjointness scans before `GO_MATERIALIZE/MODEL` can become true.
Those checks require the concrete scientific IDs and exact R0--R15 bytes, so
they cannot be produced in the only currently authorized stage.

Add a separate `GO_PREPARE` gate after CPU source/checker audit. It may
deterministically instantiate the one sealed root and invoke only the pinned
tokenizer to create overlap, length, RAW-solver, batch and FLOP manifests. It
must still forbid model calls, child formation, fits and GPU use. Then make
model/materialization-of-lived-data gates depend on that preparation receipt.

### P0.E — A few claimed literal pins are still not literal

The public actor grammar leaves `THINK <text>` without a full-match regex or
empty/body rule. The four cold invalid requests name no exact reserved node/
event bytes. `confirmation_reserved` has no allocation count. The two literal
writer seeds are never connected to the later per-stream seed formula, while
that formula does not define the byte encoding of `world` and `stage` or the
endianness meant by `low64`. These are small, but every one changes a parser,
manifest, or RNG receipt and therefore belongs in the contract.

Finally, define `imported_parameter_count` in the claimed hard FLOP formula as
an exact manifest field (total loaded parameters versus trainable parameters)
and state that the formula is a stopping budget rather than an exact profiler
identity. The asserted 248 GPU-hour/72-hour limits are valid hard stops, but
they are not derived evidence of feasibility.

## Verified arithmetic under the present ledger

The following v3 corrections are internally consistent and should be kept:

```text
route rollouts/world       12 + 18 + 16 + 22 = 68
actor calls                68 * 22 = 1,496
native reader calls        (16 + 18) * 10 = 340
cold/canary calls          7 * 60 + 6 * 70 = 840
formation calls            20 + 6 = 26
incremental preservation   2 * (32 + 8 * 29) = 528
model calls/world          1,496 + 340 + 840 + 26 + 528 = 3,230
generated tokens/world     278,528 + 54,400 + 154,368
                           + 2,880 + 81,920 = 572,096
```

D1/D2 fit, update, presentation, and maximum-padded-token totals also
recompute exactly. This arithmetic does not cure an incomplete treatment
mapping or gate; regenerate it from the repaired sole ledger even if the
numbers remain unchanged.

## Disposition

```text
REWORK_TSJ_V3  = TRUE
GO_CPU_SOURCE  = FALSE
GO_PREPARE     = FALSE
GO_MATERIALIZE = FALSE
GO_TOKENIZER   = FALSE
GO_MODEL       = FALSE
GO_FIT_OR_GPU  = FALSE
GO_CLAIM       = FALSE
```

The minimum v4 is a narrow textual repair: use treatment-invariant unit slots;
fully map ATOM fillers; reconcile diagnostic/gate roles and preservation
thresholds in the canonical ledger; add the tokenizer-only preparation stage;
and freeze the remaining parser/sentinel/seed/FLOP fields. The XOR estimand,
authentic/control split, legal whole-registry forks, ancestry, RAW construction,
active-text labeling, ITT rule, and corrected resource arithmetic need no
redesign.
