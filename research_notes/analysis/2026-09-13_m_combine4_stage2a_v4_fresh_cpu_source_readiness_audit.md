# Fresh CPU-source-readiness audit: M-COMBINE-4 Stage 2A v4

**Date:** 2026-09-13 PT

**Role:** fresh adversarial CPU-source reviewer

**Object:** commit `2f0a4f1b96029ba1194d665d38eb9e47c3c23bc5`, file
`research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md`,
verified SHA-256
`ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1`.

I read v4 from the exact commit object, its v3 parent contract at
`da6a9924629e2dc1aac757866e983086b7fc1995`, and the fresh v3 audit whose B1--B3
findings v4 repairs at
`119b63f9676c94536aeac13e283353d7093b07f9`. The parent v3 and audit bytes have
SHA-256 respectively
`da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1`
and
`026ec1d8d9c371d6948c11fc91c6c9fd936e2d3923711163a7f89047f49b8918`.
The audited commit adds only the v4 correction memo.

This was a documentation and deterministic byte/integer audit. I did not
author or run Stage-2A source, create a material root, use a tokenizer or
model, fit or mount an adapter, use a GPU, inspect sealed roots, or assess a
scientific result.

## Verdict

**GO_CPU_SOURCE after root adoption.**

V4 closes all three remaining v3 source blockers without changing the master,
role inventory, allocator, registry cardinalities, prompt/parser, certificate,
lexer, intervention panels, nulls, canaries, seed tape, dose gates, claims, or
cost caps. Two independent CPU source authors now have one disposition for
the repaired points:

- birth mismatch correction preserves reached/unresolved status and the exact
  target ledger;
- all 32 held scored first-hop EVENT rows have one explicit exception and
  golden table; and
- both path-complete CONTINUE graph vectors flag the latest goal state CURRENT,
  with exact induced radii and verified hashes.

This is authority to author the separate CPU generator, independent checker,
and in-memory tests only. It is not evidence that those sources pass, and it
does not open a durable root or any later execution.

## B1--B3 closure

| prior blocker | audit result |
|---|---|
| B1 / P0.1: recovery terminal class and relation-pair identity | **Closed.** Reached correction goes to GOAL; unresolved A/B correction goes to the exact family hub. The 16 mismatch cases split 8/8. Relation members share the failed query, block, EVENT/STEP, outcome, RECOVER address, and corrective IDs; only the two FOR leaves in `recovery_m0` differ. The second registered recovery remains a finite off-trace structural contingency. |
| B2 / P0.3: conflicting held first-EVENT placement | **Closed.** The exception is limited to the two scored start-state blocks per chain world, applies to expected and mismatch worlds, fixes the matching row at `(HH+m) mod 4`, and completely assigns the other three rows. All unscored starts and all predicted-hub blocks retain the generic rule. |
| B3 / P0.5: wrong CURRENT flags and incomplete enums | **Closed.** Both full vectors and their cores put CURRENT on goal-state `S0000`; pre-step start and intermediate hub are unflagged. The exhaustive enum table removes punctuation/case choices. Every dependent graph, radius, signature, and core byte/hash verifies. |

## Independent recovery and target enumeration

The fixed mismatch pairs remain
`p01,p03,p05,p07,p25,p27,p29,p31`. Applying the inherited `b mod 2` terminal
formula and v4 corrective destinations gives:

```text
mismatch reached       8 cases: p01,p03,p25,p27, both members
mismatch unresolved    8 cases: p05,p07,p29,p31, both members
all reached/unresolved                         32/32
fourth-target STOP/READ                        32/32
READ   96 = 64 SEEK + 32 unresolved CONTINUE
STEP   64
THINK  64 = 32 KEEP + 32 REVISE
STOP   32
TOTAL 256
```

The unresolved corrective destination remains usable: every A/B hub is in
the existing birth `Z` set and therefore owns the required 24-row INDEX
directory. Reached corrections satisfy the exact STOP condition. No role,
query, response block, or registry key is added or removed, so v3's verified
role-list and registry counts remain applicable.

For relation mismatch pairs, v4 removes the deep swap from the failed block.
Both members take row `u`, reach `surp_m0`, revise the same EVENT, and read the
same candidate-owned RECOVER query. The sole on-trace mutation is the swap of
the two FOR leaves at rows `u` and `u+2` in the shared `recovery_m0` block.
Their frozen GOT values preserve terminal class while different relevant rows
produce different corrective STEP targets. This now matches the inherited
relation/deep-swap identity contract.

## Independent Family-C table check

I regenerated all 32 records directly from:

```text
left goal  = (5*HH) mod 12
right goal = 12 + ((7*HH) mod 12)
row        = (HH + member) mod 4
```

The generated records equal the displayed table and exact CJSON byte-for-byte.
The CJSON is `1,633` bytes and hashes to
`87e9526c15056e0e715fecdc4e0e384c8439a03d7b5780ec61992b49376d8d13`.
There are no duplicate member records or unassigned candidate slots. The
exception resolves all 20 disagreements previously produced by applying the
generic formula to scored first-hop blocks, while leaving role keys and pool
assignment unchanged.

## Independent graph, radius, signature, and core check

I parsed both corrected graph CJSON values, independently rebuilt undirected
distance by making all vertices incident to a hyperedge neighbors, induced
radii 0--3, and compared those objects with the printed radius preimages.
Both suites match exactly.

TRAIN_REACHED verifies as:

```text
CURRENT state      S0000
graph              8b8ecf450b8ac2892560f5de5763920838db925d0dfe3409600497932a11290d
r0                 da8cf5e758f97683afde432afb601ed04a27858f447586290308eeea44c70381
r1                 b9988f549776661113ec3e0ce91a695c85797430a5944ab3397e2007c25fb233
r2                 2c069f9fe209d97ce5b713a0cef18feaf9425c124ba23e7fbaf9fde4d65f0445
r3                 575f38cdc30ffe58782854b906866faeb5d87f2a30a409136bad3a8e09284cfa
signature          485f6a88992cffc00184aee9c6caa0847538f3fe4d867b806ede0ac7f8785cc7
core               dd98c83c38cf984f22184960c1ba4db99ca279a1c4a3ab580a67feed3514c1ae
```

HELD_TWO_STEP verifies as:

```text
CURRENT state      S0000
graph              1e9f1f5a48adf5376660a24e19cd79b29cc9f80353155dc0cc6a943f61e39a50
r0                 4b8e9dd37a8ef832a09f8cc06e76260f560cb03e97d2c33dd6986361507d6908
r1                 e5a82e6dc73d86dd751d149f9addb6ec846a7abc6282d70c881446b91aaf3f26
r2                 6bc353834ef7cf3a32fbaf348683cf899a9f1da104e7e935d945404eac979392
r3                 5331c2439d190599785c4821ea3e94efcfeb055c4a05dc543fe7cf1e207d55dd
signature          d59b94fd9a79af2a27fff5f5e3c09b6e4c2234fc1ea64edc4579fe039d4da540
core               2acebc8a1d1e9e8d5823681a66e69706bcc7389e3dc8faceb0b4b4de017c9cb0
```

For each vector, the graph CJSON is canonical, the printed radius objects are
the exact induced subgraphs, the signature JSON contains the recomputed four
radius hashes, and the core embeds the corrected public graph. Radius 0
correctly remains unchanged because it contains only the root EVENT/PORT.

## Preserved counts, costs, claims, and authority

The case/factor inventory remains 64 cases and 32 causal pairs, with 32/32 for
family, flow, terminal class, goal side, and skin, and recovery
mismatch/MISS/irrelevant `16/8/8`. Presentation and resource arithmetic still
closes:

```text
D1 updates across fitted arms               512
D2 additional updates across arms          512
D1 model-call cap        96*29+192+48     = 3,024
D2 model-call addition   64*29+128+32     = 2,016
terminal model-call cap                      5,040
D1 generated-token cap   96*4096+240*256  = 454,656
D2 generated-token add   64*4096+160*256  = 303,104
terminal generated-token cap                 757,760
reader-model calls                           0
```

Training-token work, time, memory, and GPU-hours remain deliberately unbound.
The later claim remains limited to a lab-taught exact-text controller, with
the coherent-history clause only under the inherited CLOSED-minus-ATOM gate.
V4 changes no threshold or interpretation.

The authority boundary is exact: after root adoption, CPU source/checker/test
authoring is open. Writing a durable scientific root, materialization, real
tokenizer/model use, fitting, GPU work, sealed-root access, and scientific
claims remain closed. A fresh audit of the committed source/test/spec hashes
is still mandatory before any later opening.

## Disposition

```text
REWORK_MCOMBINE_STAGE2A_V4 = FALSE
GO_CPU_SOURCE              = TRUE_AFTER_ROOT_ADOPTION
GO_CPU_TEST                = TRUE_AFTER_ROOT_ADOPTION
GO_WRITE_ROOT              = FALSE
GO_MATERIALIZE             = FALSE
GO_MODEL_TOKENIZER         = FALSE
GO_FIT_OR_GPU              = FALSE
GO_CLAIM                   = FALSE
```

**Final ruling: GO_CPU_SOURCE after root adoption of v4's exact commit/file
hash.** Implement only the separate in-memory CPU generator/checker/tests,
preserve the tiny fixture, and bind the resulting exact source/test/spec hashes
for fresh review before materialization.
