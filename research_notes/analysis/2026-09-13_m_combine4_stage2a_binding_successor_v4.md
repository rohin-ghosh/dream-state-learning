# Binding successor v4: narrow M-COMBINE-4 Stage 2A CPU-source correction

**Date:** 2026-09-13 PT  
**Authority:** `GO_CPU_SOURCE` only.  
**Repairs:** B1--B3 in fresh audit commit
`119b63f9676c94536aeac13e283353d7093b07f9`.  
**Parent:** v3 commit `da6a9924629e2dc1aac757866e983086b7fc1995`,
file SHA-256
`da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1`.

## 1. Precedence and unchanged bytes

V4 is a correction layer, not a new experiment. V3 and its v2 parent remain
binding except for the three replacements below:

1. v3 sections 4.1--4.2 are corrected for birth STEP-mismatch destinations,
   relation-pair ownership, and exact traces;
2. v3 section 4.4 is corrected for scored chain first-hop EVENT placement; and
3. v3 sections 7.3--7.5 are corrected for enum values and CURRENT flags, with
   every dependent graph/radius/signature/core byte and hash republished here.

The material master remains exactly
`M-COMBINE-4/STAGE2A/V3/2026-09-13`; the allocation algorithm, all four role
lists, every role-list count/hash, all 352,100 allocated/reserved candidate
tokens, registry cardinalities, embedded certificate, lexer, prompt/parser,
intervention panels, target/coupling/presentation contracts, nulls, canaries,
seed labels/ordinals, D1/D2 gates, and cost caps are unchanged. V4 creates,
removes, or renames no role and changes no pool serial. In particular the v3
certificate remains authoritative at its bound v3 fragment path and hash.

```text
GO_CPU_SOURCE       = TRUE_AFTER_ROOT_ADOPTION
GO_CPU_TEST         = TRUE_AFTER_ROOT_ADOPTION
GO_WRITE_ROOT       = FALSE
GO_MATERIALIZE      = FALSE
GO_MODEL_TOKENIZER  = FALSE
GO_FIT_OR_GPU       = FALSE
GO_CLAIM            = FALSE
```

## 2. Corrected bounded birth recovery

### 2.1 Corrective destinations preserve terminal class

V3's statement that every birth surprise-corrective current-state row GOT its
FOR goal is replaced. In a reached birth case, the selected corrective row
GOT task GOAL. In an unresolved birth case, it GOT the family hub:

```text
family A, selected semantic goal g_k -> a_k
family B, selected semantic goal g_k -> b_(k mod 6)
```

For an ordinary goal-switch corrective block, every row whose AT is the
surprise state follows its own FOR goal through that rule; wrong-AT rows keep
the v3 `x_k -> x_(k+3 mod 24)` rule. Thus the unique relevant corrective row
reaches GOAL in a reached cell and the selected goal's hub in an unresolved
cell.

For a relation/deep-swap corrective target block, rows `u` and `u+2` both have
AT equal to the same surprise state. Their non-FOR fields are frozen:

```text
reached:     GOT(u) = GOT(u+2) = task GOAL
unresolved A: GOT(u) = a_j;       GOT(u+2) = a_((j+1) mod 24)
unresolved B: GOT(u) = b_(j mod 6); GOT(u+2) = b_((j+1) mod 6)
```

Member m1 swaps only their FOR leaves. Therefore both members retain the
same reached/unresolved class while selecting different STEP ports. Every
corrective port's fixed world destination equals its frozen GOT. Chain
Family-C corrective blocks remain terminal-to-goal exactly as v3 specified.

### 2.2 Relation-pair identity and recovery owners

Every mismatch pair still owns exactly the two v3 predicted/surprise node
pairs, two mistaken candidates, two registered candidate RECOVER queries, and
two four-row recovery blocks. Counts and role keys do not change.

For a goal-switch mismatch pair, member m selects its own scored goal's
mistaken candidate in that goal's start block. That candidate predicts
`pred_m`, actually reaches `surp_m`, and its registered candidate RECOVER
query owns `recovery_m`. Both mistaken blocks/registrations exist in the one
shared world; each task executes only the goal-selected one.

For a relation/deep-swap mismatch pair, both member variants have byte-
identical task, failed start query, failed four-row block, candidate IDs,
non-FOR fields, and base world. The failed block does **not** receive the deep
swap. It has row `u` matching GOAL+CURRENT and row `u+2` matching CURRENT only.
Both are pre-authored mistaken candidates:

```text
row u       GOT pred_m0, world -> surp_m0, RECOVER -> recovery_m0 query
row u+2     GOT pred_m1, world -> surp_m1, RECOVER -> recovery_m1 query
```

Both members therefore execute the same failed EVENT/STEP, observe the same
`surp_m0`, emit REVISE on the same event, and target the same registered
RECOVER query. The returned `surp_m0/.../recovery_m0` block is the sole
target-bearing deep-swap block: its rows u/u+2 use section 2.1 destinations,
and member m1 swaps only those two FOR leaves. All IDs, AT, GOT, DID, RECOVER,
EVIDENCE, row order, and every other store/world byte remain identical.

The `recovery_m1` block remains a registered structural contingency for the
second mistaken candidate and is identical across member variants; it is not
on either scored trace. Its four rows use the ordinary terminal-class rule in
section 2.1. Its nested RECOVER operands and those in `recovery_m0` remain
unregistered. No recursive recovery or third block exists.

### 2.3 Total mismatch target traces and arithmetic

For every goal-switch mismatch member, the exact public causal sequence is:

```text
failed selected query -> selected mistaken event -> WORLD surp_m
-> THINK REVISE failed_event -> ACK
-> READ RELATION failed_event.RECOVER -> recovery_m block
-> STEP unique matching corrective port -> WORLD corrective GOT
-> STOP iff CURRENT==GOAL, otherwise READ INDEX CURRENT
```

For every relation mismatch member the same sequence uses shared `surp_m0`,
shared failed event, shared RECOVER query, and member-specific relevant row of
the FOR-swapped `recovery_m0` block. These are actor targets only at the same
four v2 decision points: REVISE, corrective READ, corrective STEP, and
STOP/READ. WORLD/ACK and earlier failed actions remain loss-masked prefix.

Exactly eight mismatch cases are reached
(`p01,p03,p25,p27`, two members each) and eight are unresolved
(`p05,p07,p29,p31`, two members each). The former contribute eight fourth-
target STOPs; the latter contribute eight fourth-target READ INDEX actions.
Together with unchanged cases, this restores exactly:

```text
reached/unresolved cases 32/32
READ   96 = 64 SEEK + 32 unresolved CONTINUE
STEP   64
THINK  64 = 32 KEEP + 32 REVISE
STOP   32
TOTAL 256
```

The v3 registry counts remain exact because both relation recovery queries
remain registered even though only the first lies on scored traces.

## 3. Corrected Family-C first-hop placement

V3's generic `v=(3*j+state_ordinal+skin) mod 4` remains total except for the
two scored **start-state first-hop** blocks in every `dose_chain/hHH` world.
For scored member m's goal, set:

```text
c = (HH + m) mod 4
row c       AT s       FOR scored goal       (both matching)
row c+1     AT s       FOR next goal          (CURRENT only)
row c+2     AT x_j     FOR scored goal        (GOAL only)
row c+3     AT x_(j+1) FOR goal j+2           (neither)
```

Candidate arithmetic is modulo four and goal arithmetic modulo 24. This
exception applies identically in expected and mismatch worlds. In a mismatch
world only row c is the already-bound mistaken first-hop event. The other
three rows use v3's ordinary Family-C destinations/world edges. All 22
unscored start blocks and every predicted-hub block, including the scored
second-hop blocks, use v3's generic formula without exception.

The canonical 32-row table is ordered by h00/m0,h00/m1,...,h15/m1:

| world | member | goal | row | world | member | goal | row |
|---|---|---|---:|---|---|---|---:|
| h00 | m0 | g00 | 0 | h00 | m1 | g12 | 1 |
| h01 | m0 | g05 | 1 | h01 | m1 | g19 | 2 |
| h02 | m0 | g10 | 2 | h02 | m1 | g14 | 3 |
| h03 | m0 | g03 | 3 | h03 | m1 | g21 | 0 |
| h04 | m0 | g08 | 0 | h04 | m1 | g16 | 1 |
| h05 | m0 | g01 | 1 | h05 | m1 | g23 | 2 |
| h06 | m0 | g06 | 2 | h06 | m1 | g18 | 3 |
| h07 | m0 | g11 | 3 | h07 | m1 | g13 | 0 |
| h08 | m0 | g04 | 0 | h08 | m1 | g20 | 1 |
| h09 | m0 | g09 | 1 | h09 | m1 | g15 | 2 |
| h10 | m0 | g02 | 2 | h10 | m1 | g22 | 3 |
| h11 | m0 | g07 | 3 | h11 | m1 | g17 | 0 |
| h12 | m0 | g00 | 0 | h12 | m1 | g12 | 1 |
| h13 | m0 | g05 | 1 | h13 | m1 | g19 | 2 |
| h14 | m0 | g10 | 2 | h14 | m1 | g14 | 3 |
| h15 | m0 | g03 | 3 | h15 | m1 | g21 | 0 |

Its CJSON is an array of objects with keys `goal,member,row,world` in that
order under CJSON key sorting, no final LF:

```text
[{"goal":"g00","member":"m0","row":0,"world":"h00"},{"goal":"g12","member":"m1","row":1,"world":"h00"},{"goal":"g05","member":"m0","row":1,"world":"h01"},{"goal":"g19","member":"m1","row":2,"world":"h01"},{"goal":"g10","member":"m0","row":2,"world":"h02"},{"goal":"g14","member":"m1","row":3,"world":"h02"},{"goal":"g03","member":"m0","row":3,"world":"h03"},{"goal":"g21","member":"m1","row":0,"world":"h03"},{"goal":"g08","member":"m0","row":0,"world":"h04"},{"goal":"g16","member":"m1","row":1,"world":"h04"},{"goal":"g01","member":"m0","row":1,"world":"h05"},{"goal":"g23","member":"m1","row":2,"world":"h05"},{"goal":"g06","member":"m0","row":2,"world":"h06"},{"goal":"g18","member":"m1","row":3,"world":"h06"},{"goal":"g11","member":"m0","row":3,"world":"h07"},{"goal":"g13","member":"m1","row":0,"world":"h07"},{"goal":"g04","member":"m0","row":0,"world":"h08"},{"goal":"g20","member":"m1","row":1,"world":"h08"},{"goal":"g09","member":"m0","row":1,"world":"h09"},{"goal":"g15","member":"m1","row":2,"world":"h09"},{"goal":"g02","member":"m0","row":2,"world":"h10"},{"goal":"g22","member":"m1","row":3,"world":"h10"},{"goal":"g07","member":"m0","row":3,"world":"h11"},{"goal":"g17","member":"m1","row":0,"world":"h11"},{"goal":"g00","member":"m0","row":0,"world":"h12"},{"goal":"g12","member":"m1","row":1,"world":"h12"},{"goal":"g05","member":"m0","row":1,"world":"h13"},{"goal":"g19","member":"m1","row":2,"world":"h13"},{"goal":"g10","member":"m0","row":2,"world":"h14"},{"goal":"g14","member":"m1","row":3,"world":"h14"},{"goal":"g03","member":"m0","row":3,"world":"h15"},{"goal":"g21","member":"m1","row":0,"world":"h15"}]
```

It is 1,633 bytes with SHA-256
`87e9526c15056e0e715fecdc4e0e384c8439a03d7b5780ec61992b49376d8d13`.
No role-list or allocator hash changes because only row field placement changes.

## 4. Corrected canonical enums and CONTINUE vectors

### 4.1 Exhaustive core enums

The only core string values are:

```text
phase:             SEEK PROSPECT READ_CHECK STEP_CHECK CONTINUE
flow:              ORDINARY RECOVERY
recovery_subtype:  NONE STRICT_MISS IRRELEVANT_RETURN STEP_OUTCOME_MISMATCH
family_motif:      A_PRIVATE_SPOKES B_BUCKET_MERGES C_CROSSING_WEAVE
goal_side:         LEFT RIGHT
terminal_class:    REACHED UNRESOLVED
```

No slash, hyphen, space, lowercase, alias, or display label is accepted.
`predicted_actual_match` and position nullability remain v3 section 7.3.
Canonicalization and hash-domain prefixes remain `M2A-GRAPH-V3`,
`M2A-RADIUS-V3`, `M2A-SIGNATURE-V3`, and `M2A-CORE-V3`; changing the CURRENT
flag changes dependent bytes/hashes, not the canonicalization version.

### 4.2 Corrected TRAIN_REACHED

This path-complete CONTINUE vector flags the latest goal STATE S0000 CURRENT;
the pre-step start S0001 has no CURRENT flag. Corrected graph CJSON is:

```text
{"edges":[{"heads":["E0000"],"label":"CONTAINS","tails":["Q0001"]},{"heads":["G0000"],"label":"FOR","tails":["E0000"]},{"heads":["P0000"],"label":"DID","tails":["E0000"]},{"heads":["Q0000"],"label":"RECOVER","tails":["E0000"]},{"heads":["Q0001"],"label":"INDEXES","tails":["S0001","G0000"]},{"heads":["R0000"],"label":"EVIDENCE","tails":["E0000"]},{"heads":["S0000"],"label":"GOT","tails":["E0000"]},{"heads":["S0000"],"label":"WORLD","tails":["S0001","P0000"]},{"heads":["S0001"],"label":"AT","tails":["E0000"]}],"vertices":[{"alias":"E0000","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0000","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0000","flags":[],"type":"QUERY"},{"alias":"Q0001","flags":[],"type":"QUERY"},{"alias":"R0000","flags":[],"type":"RECEIPT"},{"alias":"S0000","flags":["CURRENT"],"type":"STATE"},{"alias":"S0001","flags":[],"type":"STATE"}]}
```

Graph hash:
`8b8ecf450b8ac2892560f5de5763920838db925d0dfe3409600497932a11290d`.
Radius 0 CJSON is unchanged:

```text
{"edges":[{"heads":["P0000"],"label":"DID","tails":["E0000"]}],"vertices":[{"alias":"E0000","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"P0000","flags":["ROOT_PORT"],"type":"PORT"}]}
```

Radius 1, 2, and 3 CJSON are each the full corrected graph above. Radius hashes
and signature JSON/hash are:

```text
da8cf5e758f97683afde432afb601ed04a27858f447586290308eeea44c70381
b9988f549776661113ec3e0ce91a695c85797430a5944ab3397e2007c25fb233
2c069f9fe209d97ce5b713a0cef18feaf9425c124ba23e7fbaf9fde4d65f0445
575f38cdc30ffe58782854b906866faeb5d87f2a30a409136bad3a8e09284cfa
{"r0":"da8cf5e758f97683afde432afb601ed04a27858f447586290308eeea44c70381","r1":"b9988f549776661113ec3e0ce91a695c85797430a5944ab3397e2007c25fb233","r2":"2c069f9fe209d97ce5b713a0cef18feaf9425c124ba23e7fbaf9fde4d65f0445","r3":"575f38cdc30ffe58782854b906866faeb5d87f2a30a409136bad3a8e09284cfa"}
485f6a88992cffc00184aee9c6caa0847538f3fe4d867b806ede0ac7f8785cc7
```

Corrected core CJSON/hash are:

```text
{"actual_route_depth":1,"family_motif":"A_PRIVATE_SPOKES","flow":"ORDINARY","goal_side":"LEFT","phase":"CONTINUE","predicted_actual_match":true,"public_graph":{"edges":[{"heads":["E0000"],"label":"CONTAINS","tails":["Q0001"]},{"heads":["G0000"],"label":"FOR","tails":["E0000"]},{"heads":["P0000"],"label":"DID","tails":["E0000"]},{"heads":["Q0000"],"label":"RECOVER","tails":["E0000"]},{"heads":["Q0001"],"label":"INDEXES","tails":["S0001","G0000"]},{"heads":["R0000"],"label":"EVIDENCE","tails":["E0000"]},{"heads":["S0000"],"label":"GOT","tails":["E0000"]},{"heads":["S0000"],"label":"WORLD","tails":["S0001","P0000"]},{"heads":["S0001"],"label":"AT","tails":["E0000"]}],"vertices":[{"alias":"E0000","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0000","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0000","flags":[],"type":"QUERY"},{"alias":"Q0001","flags":[],"type":"QUERY"},{"alias":"R0000","flags":[],"type":"RECEIPT"},{"alias":"S0000","flags":["CURRENT"],"type":"STATE"},{"alias":"S0001","flags":[],"type":"STATE"}]},"recovery_subtype":"NONE","relevant_candidate_display_position":null,"skin":0,"terminal_class":"REACHED","typed_vertex_counts":{"EVENT":1,"GOAL":1,"PORT":1,"QUERY":2,"RECEIPT":1,"STATE":2}}
dd98c83c38cf984f22184960c1ba4db99ca279a1c4a3ab580a67feed3514c1ae
```

### 4.3 Corrected HELD_TWO_STEP

This path-complete CONTINUE vector flags latest goal STATE S0000 CURRENT; hub
S0001 and pre-step start S0002 have no CURRENT flag. Corrected full graph is:

```text
{"edges":[{"heads":["E0000"],"label":"CONTAINS","tails":["Q0001"]},{"heads":["E0001"],"label":"CONTAINS","tails":["Q0003"]},{"heads":["G0000"],"label":"FOR","tails":["E0000"]},{"heads":["G0000"],"label":"FOR","tails":["E0001"]},{"heads":["P0000"],"label":"DID","tails":["E0000"]},{"heads":["P0001"],"label":"DID","tails":["E0001"]},{"heads":["Q0000"],"label":"RECOVER","tails":["E0000"]},{"heads":["Q0001"],"label":"INDEXES","tails":["S0001","G0000"]},{"heads":["Q0002"],"label":"RECOVER","tails":["E0001"]},{"heads":["Q0003"],"label":"INDEXES","tails":["S0002","G0000"]},{"heads":["R0000"],"label":"EVIDENCE","tails":["E0000"]},{"heads":["R0001"],"label":"EVIDENCE","tails":["E0001"]},{"heads":["S0000"],"label":"GOT","tails":["E0000"]},{"heads":["S0000"],"label":"WORLD","tails":["S0001","P0000"]},{"heads":["S0001"],"label":"AT","tails":["E0000"]},{"heads":["S0001"],"label":"GOT","tails":["E0001"]},{"heads":["S0001"],"label":"WORLD","tails":["S0002","P0001"]},{"heads":["S0002"],"label":"AT","tails":["E0001"]}],"vertices":[{"alias":"E0000","flags":[],"type":"EVENT"},{"alias":"E0001","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0000","flags":[],"type":"PORT"},{"alias":"P0001","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0000","flags":[],"type":"QUERY"},{"alias":"Q0001","flags":[],"type":"QUERY"},{"alias":"Q0002","flags":[],"type":"QUERY"},{"alias":"Q0003","flags":[],"type":"QUERY"},{"alias":"R0000","flags":[],"type":"RECEIPT"},{"alias":"R0001","flags":[],"type":"RECEIPT"},{"alias":"S0000","flags":["CURRENT"],"type":"STATE"},{"alias":"S0001","flags":[],"type":"STATE"},{"alias":"S0002","flags":[],"type":"STATE"}]}
```

Graph hash:
`1e9f1f5a48adf5376660a24e19cd79b29cc9f80353155dc0cc6a943f61e39a50`.
Radius CJSON preimages follow; `rN=` is not part of R_N.

```text
r0={"edges":[{"heads":["P0001"],"label":"DID","tails":["E0001"]}],"vertices":[{"alias":"E0001","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"P0001","flags":["ROOT_PORT"],"type":"PORT"}]}
r1={"edges":[{"heads":["E0001"],"label":"CONTAINS","tails":["Q0003"]},{"heads":["G0000"],"label":"FOR","tails":["E0001"]},{"heads":["P0001"],"label":"DID","tails":["E0001"]},{"heads":["Q0002"],"label":"RECOVER","tails":["E0001"]},{"heads":["Q0003"],"label":"INDEXES","tails":["S0002","G0000"]},{"heads":["R0001"],"label":"EVIDENCE","tails":["E0001"]},{"heads":["S0001"],"label":"GOT","tails":["E0001"]},{"heads":["S0001"],"label":"WORLD","tails":["S0002","P0001"]},{"heads":["S0002"],"label":"AT","tails":["E0001"]}],"vertices":[{"alias":"E0001","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0001","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0002","flags":[],"type":"QUERY"},{"alias":"Q0003","flags":[],"type":"QUERY"},{"alias":"R0001","flags":[],"type":"RECEIPT"},{"alias":"S0001","flags":[],"type":"STATE"},{"alias":"S0002","flags":[],"type":"STATE"}]}
r2={"edges":[{"heads":["E0000"],"label":"CONTAINS","tails":["Q0001"]},{"heads":["E0001"],"label":"CONTAINS","tails":["Q0003"]},{"heads":["G0000"],"label":"FOR","tails":["E0000"]},{"heads":["G0000"],"label":"FOR","tails":["E0001"]},{"heads":["P0000"],"label":"DID","tails":["E0000"]},{"heads":["P0001"],"label":"DID","tails":["E0001"]},{"heads":["Q0001"],"label":"INDEXES","tails":["S0001","G0000"]},{"heads":["Q0002"],"label":"RECOVER","tails":["E0001"]},{"heads":["Q0003"],"label":"INDEXES","tails":["S0002","G0000"]},{"heads":["R0001"],"label":"EVIDENCE","tails":["E0001"]},{"heads":["S0000"],"label":"GOT","tails":["E0000"]},{"heads":["S0000"],"label":"WORLD","tails":["S0001","P0000"]},{"heads":["S0001"],"label":"AT","tails":["E0000"]},{"heads":["S0001"],"label":"GOT","tails":["E0001"]},{"heads":["S0001"],"label":"WORLD","tails":["S0002","P0001"]},{"heads":["S0002"],"label":"AT","tails":["E0001"]}],"vertices":[{"alias":"E0000","flags":[],"type":"EVENT"},{"alias":"E0001","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0000","flags":[],"type":"PORT"},{"alias":"P0001","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0001","flags":[],"type":"QUERY"},{"alias":"Q0002","flags":[],"type":"QUERY"},{"alias":"Q0003","flags":[],"type":"QUERY"},{"alias":"R0001","flags":[],"type":"RECEIPT"},{"alias":"S0000","flags":["CURRENT"],"type":"STATE"},{"alias":"S0001","flags":[],"type":"STATE"},{"alias":"S0002","flags":[],"type":"STATE"}]}
r3={"edges":[{"heads":["E0000"],"label":"CONTAINS","tails":["Q0001"]},{"heads":["E0001"],"label":"CONTAINS","tails":["Q0003"]},{"heads":["G0000"],"label":"FOR","tails":["E0000"]},{"heads":["G0000"],"label":"FOR","tails":["E0001"]},{"heads":["P0000"],"label":"DID","tails":["E0000"]},{"heads":["P0001"],"label":"DID","tails":["E0001"]},{"heads":["Q0000"],"label":"RECOVER","tails":["E0000"]},{"heads":["Q0001"],"label":"INDEXES","tails":["S0001","G0000"]},{"heads":["Q0002"],"label":"RECOVER","tails":["E0001"]},{"heads":["Q0003"],"label":"INDEXES","tails":["S0002","G0000"]},{"heads":["R0000"],"label":"EVIDENCE","tails":["E0000"]},{"heads":["R0001"],"label":"EVIDENCE","tails":["E0001"]},{"heads":["S0000"],"label":"GOT","tails":["E0000"]},{"heads":["S0000"],"label":"WORLD","tails":["S0001","P0000"]},{"heads":["S0001"],"label":"AT","tails":["E0000"]},{"heads":["S0001"],"label":"GOT","tails":["E0001"]},{"heads":["S0001"],"label":"WORLD","tails":["S0002","P0001"]},{"heads":["S0002"],"label":"AT","tails":["E0001"]}],"vertices":[{"alias":"E0000","flags":[],"type":"EVENT"},{"alias":"E0001","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0000","flags":[],"type":"PORT"},{"alias":"P0001","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0000","flags":[],"type":"QUERY"},{"alias":"Q0001","flags":[],"type":"QUERY"},{"alias":"Q0002","flags":[],"type":"QUERY"},{"alias":"Q0003","flags":[],"type":"QUERY"},{"alias":"R0000","flags":[],"type":"RECEIPT"},{"alias":"R0001","flags":[],"type":"RECEIPT"},{"alias":"S0000","flags":["CURRENT"],"type":"STATE"},{"alias":"S0001","flags":[],"type":"STATE"},{"alias":"S0002","flags":[],"type":"STATE"}]}
```

Radius hashes, signature JSON, and signature hash are:

```text
4b8e9dd37a8ef832a09f8cc06e76260f560cb03e97d2c33dd6986361507d6908
e5a82e6dc73d86dd751d149f9addb6ec846a7abc6282d70c881446b91aaf3f26
6bc353834ef7cf3a32fbaf348683cf899a9f1da104e7e935d945404eac979392
5331c2439d190599785c4821ea3e94efcfeb055c4a05dc543fe7cf1e207d55dd
{"r0":"4b8e9dd37a8ef832a09f8cc06e76260f560cb03e97d2c33dd6986361507d6908","r1":"e5a82e6dc73d86dd751d149f9addb6ec846a7abc6282d70c881446b91aaf3f26","r2":"6bc353834ef7cf3a32fbaf348683cf899a9f1da104e7e935d945404eac979392","r3":"5331c2439d190599785c4821ea3e94efcfeb055c4a05dc543fe7cf1e207d55dd"}
d59b94fd9a79af2a27fff5f5e3c09b6e4c2234fc1ea64edc4579fe039d4da540
```

Corrected core CJSON/hash are:

```text
{"actual_route_depth":2,"family_motif":"C_CROSSING_WEAVE","flow":"ORDINARY","goal_side":"LEFT","phase":"CONTINUE","predicted_actual_match":true,"public_graph":{"edges":[{"heads":["E0000"],"label":"CONTAINS","tails":["Q0001"]},{"heads":["E0001"],"label":"CONTAINS","tails":["Q0003"]},{"heads":["G0000"],"label":"FOR","tails":["E0000"]},{"heads":["G0000"],"label":"FOR","tails":["E0001"]},{"heads":["P0000"],"label":"DID","tails":["E0000"]},{"heads":["P0001"],"label":"DID","tails":["E0001"]},{"heads":["Q0000"],"label":"RECOVER","tails":["E0000"]},{"heads":["Q0001"],"label":"INDEXES","tails":["S0001","G0000"]},{"heads":["Q0002"],"label":"RECOVER","tails":["E0001"]},{"heads":["Q0003"],"label":"INDEXES","tails":["S0002","G0000"]},{"heads":["R0000"],"label":"EVIDENCE","tails":["E0000"]},{"heads":["R0001"],"label":"EVIDENCE","tails":["E0001"]},{"heads":["S0000"],"label":"GOT","tails":["E0000"]},{"heads":["S0000"],"label":"WORLD","tails":["S0001","P0000"]},{"heads":["S0001"],"label":"AT","tails":["E0000"]},{"heads":["S0001"],"label":"GOT","tails":["E0001"]},{"heads":["S0001"],"label":"WORLD","tails":["S0002","P0001"]},{"heads":["S0002"],"label":"AT","tails":["E0001"]}],"vertices":[{"alias":"E0000","flags":[],"type":"EVENT"},{"alias":"E0001","flags":["ROOT_EVENT"],"type":"EVENT"},{"alias":"G0000","flags":["GOAL"],"type":"GOAL"},{"alias":"P0000","flags":[],"type":"PORT"},{"alias":"P0001","flags":["ROOT_PORT"],"type":"PORT"},{"alias":"Q0000","flags":[],"type":"QUERY"},{"alias":"Q0001","flags":[],"type":"QUERY"},{"alias":"Q0002","flags":[],"type":"QUERY"},{"alias":"Q0003","flags":[],"type":"QUERY"},{"alias":"R0000","flags":[],"type":"RECEIPT"},{"alias":"R0001","flags":[],"type":"RECEIPT"},{"alias":"S0000","flags":["CURRENT"],"type":"STATE"},{"alias":"S0001","flags":[],"type":"STATE"},{"alias":"S0002","flags":[],"type":"STATE"}]},"recovery_subtype":"NONE","relevant_candidate_display_position":null,"skin":0,"terminal_class":"REACHED","typed_vertex_counts":{"EVENT":2,"GOAL":1,"PORT":2,"QUERY":4,"RECEIPT":2,"STATE":3}}
2acebc8a1d1e9e8d5823681a66e69706bcc7389e3dc8faceb0b4b4de017c9cb0
```

## 5. CPU checks and final disposition

The v3 CPU gate is retained with these additional exact checks:

1. enumerate all 16 mismatch cases and require terminal status `8/8`, fourth
   targets STOP/READ `8/8`, and overall target totals `96/64/64/32`;
2. for every relation mismatch pair, byte-diff member stores and require
   exactly the two FOR leaves in `recovery_m0`, a shared failed event/query/
   outcome/RECOVER address, different corrective STEP targets, and no other
   member difference;
3. require every goal-switch mismatch task to use its corresponding m-owned
   failed/recovery roles and terminal-class destination;
4. require all 32 chain scored first-hop rows to reproduce the table/CJSON/
   hash in section 3, every other row to use the generic rule, and role lists/
   counts/hashes to remain exactly v3;
5. require exactly one CURRENT flag in each decision graph, on latest public
   CURRENT, and reproduce every corrected graph/radius/signature/core byte and
   hash in section 4; and
6. reject every core enum string outside section 4.1.

Independent arithmetic re-enumeration gives:

```text
cases 64, targets 256, factors 32/32
recovery mismatch/MISS/irrelevant 16/8/8
mismatch reached/unresolved 8/8
all fourth-target STOP/READ 32/32
READ/STEP/THINK/STOP 96/64/64/32
D1 calls/tokens 3,024 / 454,656
D2 add calls/tokens 2,016 / 303,104
terminal calls/tokens 5,040 / 757,760
```

No source, material root, tokenizer, model, adapter, process, or GPU was
created or invoked for this correction. No impossible or scientifically
material source-choice gap is known after B1--B3. Prospective fixed-root
collision, separation, null, topology, BASE, context, or authenticated-runtime
failures still stop the experiment without reseeding or repair.

## Final ruling

**GO_CPU_SOURCE after root adoption of this exact memo hash.** Astra may author
and run in-memory CPU tests for the separate Stage-2A generator/checker. A
fresh audit of committed source/test/spec hashes remains mandatory.

**GO_WRITE_ROOT, GO_MATERIALIZE, GO_MODEL_TOKENIZER, GO_FIT_OR_GPU, and
GO_CLAIM remain FALSE.**

