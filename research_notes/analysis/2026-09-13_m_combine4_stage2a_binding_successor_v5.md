# Binding successor v5: intervention route-position corrigendum

**Date:** 2026-09-13 PT  
**Authority:** `GO_CPU_SOURCE` only.  
**Parent:** v4 commit `2ce7000a76381f5c0bfecf26e9787e9119986b62`,
file SHA-256
`ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1`.

## 1. One correction and precedence

V5 changes only the intervention route-position equation in v3 section 4.3,
inherited through v4. Replace:

```text
r0 = (3*k+t) mod 24
r1 = r0+12
```

with:

```text
r0 = (3*k+t) mod 24
r1 = (r0+12) mod 24
```

Both positions are zero-based indices into the length-24 rendered ROUTE array.
They are always in `0..23`, differ by exactly 12 modulo 24, and cannot collide.
Put semantic goal `j0=(3*k+t) mod 12` at r0 and goal
`j1=12+((5*k+t) mod 12)` at r1. Fill remaining goals and positions numeric-
ascending exactly as v3 specifies. This equation agrees with the v2 source
design and supersedes only v3's missing final modulo.

Sixteen pairs with r0 below 12 retain their already valid positions. Sixteen
pairs with r0 at least 12 wrap r1 into `0..11`. The invalid values `24..35`
never name array positions and never enter material, hashes, or custody.

## 2. Canonical corrected placement bytes

Transition order is `SEEK,PROSPECT,CHECK,CONTINUE`; within a transition k is
0..7. The canonical placement object is a 32-element array of CJSON objects
with exactly keys `goal0,goal1,k,position0,position1,transition`. Its exact
bytes, with no terminal LF, are:

```text
[{"goal0":"g00","goal1":"g12","k":0,"position0":0,"position1":12,"transition":"SEEK"},{"goal0":"g03","goal1":"g17","k":1,"position0":3,"position1":15,"transition":"SEEK"},{"goal0":"g06","goal1":"g22","k":2,"position0":6,"position1":18,"transition":"SEEK"},{"goal0":"g09","goal1":"g15","k":3,"position0":9,"position1":21,"transition":"SEEK"},{"goal0":"g00","goal1":"g20","k":4,"position0":12,"position1":0,"transition":"SEEK"},{"goal0":"g03","goal1":"g13","k":5,"position0":15,"position1":3,"transition":"SEEK"},{"goal0":"g06","goal1":"g18","k":6,"position0":18,"position1":6,"transition":"SEEK"},{"goal0":"g09","goal1":"g23","k":7,"position0":21,"position1":9,"transition":"SEEK"},{"goal0":"g01","goal1":"g13","k":0,"position0":1,"position1":13,"transition":"PROSPECT"},{"goal0":"g04","goal1":"g18","k":1,"position0":4,"position1":16,"transition":"PROSPECT"},{"goal0":"g07","goal1":"g23","k":2,"position0":7,"position1":19,"transition":"PROSPECT"},{"goal0":"g10","goal1":"g16","k":3,"position0":10,"position1":22,"transition":"PROSPECT"},{"goal0":"g01","goal1":"g21","k":4,"position0":13,"position1":1,"transition":"PROSPECT"},{"goal0":"g04","goal1":"g14","k":5,"position0":16,"position1":4,"transition":"PROSPECT"},{"goal0":"g07","goal1":"g19","k":6,"position0":19,"position1":7,"transition":"PROSPECT"},{"goal0":"g10","goal1":"g12","k":7,"position0":22,"position1":10,"transition":"PROSPECT"},{"goal0":"g02","goal1":"g14","k":0,"position0":2,"position1":14,"transition":"CHECK"},{"goal0":"g05","goal1":"g19","k":1,"position0":5,"position1":17,"transition":"CHECK"},{"goal0":"g08","goal1":"g12","k":2,"position0":8,"position1":20,"transition":"CHECK"},{"goal0":"g11","goal1":"g17","k":3,"position0":11,"position1":23,"transition":"CHECK"},{"goal0":"g02","goal1":"g22","k":4,"position0":14,"position1":2,"transition":"CHECK"},{"goal0":"g05","goal1":"g15","k":5,"position0":17,"position1":5,"transition":"CHECK"},{"goal0":"g08","goal1":"g20","k":6,"position0":20,"position1":8,"transition":"CHECK"},{"goal0":"g11","goal1":"g13","k":7,"position0":23,"position1":11,"transition":"CHECK"},{"goal0":"g03","goal1":"g15","k":0,"position0":3,"position1":15,"transition":"CONTINUE"},{"goal0":"g06","goal1":"g20","k":1,"position0":6,"position1":18,"transition":"CONTINUE"},{"goal0":"g09","goal1":"g13","k":2,"position0":9,"position1":21,"transition":"CONTINUE"},{"goal0":"g00","goal1":"g18","k":3,"position0":12,"position1":0,"transition":"CONTINUE"},{"goal0":"g03","goal1":"g23","k":4,"position0":15,"position1":3,"transition":"CONTINUE"},{"goal0":"g06","goal1":"g16","k":5,"position0":18,"position1":6,"transition":"CONTINUE"},{"goal0":"g09","goal1":"g21","k":6,"position0":21,"position1":9,"transition":"CONTINUE"},{"goal0":"g00","goal1":"g14","k":7,"position0":0,"position1":12,"transition":"CONTINUE"}]
```

The byte length is 2,797 and SHA-256 is
`1177452578a33783e9132a9948106cdf553749d3d01493669cae3dccc67ac8f3`.

## 3. Dependency and authority audit

This correction changes rendered ROUTE row order for the 16 wrapped
intervention pairs. It does not change any role or allocated public token.
Therefore all v3 role-list counts/hashes, pool counts, registries, world edges,
target totals, intervention JSON-pointer allowlists, chain placement, chain
placement CJSON/hash, graph/radius/signature/core vectors, certificate/lexer,
null definitions, seed ordinals, D1/D2 gates, and cost caps remain unchanged.
In particular v4's chain table remains 32 rows, 1,633 bytes, SHA-256
`87e9526c15056e0e715fecdc4e0e384c8439a03d7b5780ec61992b49376d8d13`.

The source/checker CPU gate must derive all 32 placement records from the
corrected formula, match the bytes/hash above, prove r0/r1 are distinct and
in range, and prove the other 22 positions contain the other 22 goals exactly
once. The executed one-turn null gates use these corrected public row orders;
no null score is guessed or acceptance-tuned here.

No source, material root, tokenizer, model, adapter, fit, decode, or GPU was
authored or invoked for this corrigendum.

## Final ruling

**GO_CPU_SOURCE after root adoption of this exact v5 memo hash.** A fresh
source audit remains required before materialization.

**GO_WRITE_ROOT, GO_MATERIALIZE, GO_MODEL_TOKENIZER, GO_FIT_OR_GPU, and
GO_CLAIM remain FALSE.**
