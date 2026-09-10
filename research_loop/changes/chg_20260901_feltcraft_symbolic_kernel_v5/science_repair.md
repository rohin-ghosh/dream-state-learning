# FeltCraft symbolic kernel v5: science exactness repair

Status: governance proposal only. This artifact is not implementation authority,
an executed test, a runtime receipt, or scientific evidence.

## Scope and provenance

This repair addresses only V4 consensus resolutions R03 and R04 and the golden
report fields that those two resolutions necessarily change. It was derived by
reading the complete V4 proposal bundle, including the V4 consensus with
SHA-256 `682a6b53dce625283df32b82bad559ca03e5ec77e64f36279b1da8fd119ab12e`,
the V4 contract with SHA-256
`e3ad2936c8288e0e5815d779d400db389b0e354f1cbfc513184d7a9088487ea3`,
the V4 golden with SHA-256
`f14fbf5de43926b19ad8c19dc71a5d0d6a8fcc37ffbe310b60d4d8d0475c6b51`,
and the V3 consensus and contract where the same representation and boundary
issues first arose. The V4 architecture-change hash is
`fa5ef77c127b7fe614ef33875d55a4099a023bec8fc6a8a1dd98db5f0fbf2a8e`.

The exact machine-readable vectors, negative fixtures, counts, and proposed
golden fragment are in `golden_vectors.json`. JSON arrays in that artifact are
the serialization of normative immutable tuples; they do not authorize mutable
runtime lists.

## Exact direction of pi and rendering equations

Let the descriptor orders be

```text
D_R   = (DR0,DR1,DR2,DR3)
D_I   = (DI0,DI1)
D_T   = (DT0,DT1)
D     = D_R || D_I || D_T
D_out = (DI0,DI1,DT0,DT1)
```

and the role orders be the corresponding
`R=(R0,R1,R2,R3)`, `I=(I0,I1)`, and `T=(T0,T1)`. An alignment is normatively

```text
pi : descriptors -> roles
```

and is represented by the eight-tuple
`(pi(DR0),...,pi(DT1))` in `D` order. It is never represented as a
role-to-descriptor tuple. If `r`, `i`, and `t` are the zero-based lexicographic
ranks of the raw, intermediate, and top permutations in their literal orders,
then the alignment index is exactly

```text
index(pi) = 4*r + 2*i + t.
```

Let `ingredients(o)=(a_o,b_o)` be the role-space ingredient pair for recipe
output role `o`. Define the descriptor-space edge at output descriptor `d` by

```text
EDGE_pi(d) =
  (d, sort_D(pi^-1(a_pi(d)), pi^-1(b_pi(d))))
```

where `sort_D` is applied only after both role ingredients have been mapped by
`pi^-1`. Equivalently, render every role triple `(o,a_o,b_o)` as
`(pi^-1(o),sort_D(pi^-1(a_o),pi^-1(b_o)))`, then order the four rendered
triples by `D_out`. The normative derived objects are

```text
GRAPH(pi) = (EDGE_pi(DI0), EDGE_pi(DI1),
             EDGE_pi(DT0), EDGE_pi(DT1))
CAL(pi)   = (EDGE_pi(DI0), EDGE_pi(DI1))
TOP(pi,g) = the final two fields of EDGE_pi(g), g in (DT0,DT1).
```

These equations also resolve intermediate and top swaps: the recipe selected
for output descriptor `d` is the recipe whose output role is `pi(d)`. Sorting
role names before inverse rendering, applying `pi` instead of `pi^-1`, or
interpreting the stored alignment tuple in the opposite direction is wrong.

## Independent direction sentinel and vector derivation

The first four alignments contain only identity or two-element swaps, so their
maps are self-inverse and cannot alone expose a direction reversal. Index 12 is
the earliest alignment with a non-self-inverse raw permutation:

```text
pi_12 raw values = (R0,R2,R3,R1)
pi_12^-1         = (R0->DR0,R1->DR3,R2->DR1,R3->DR2)
```

Correct inverse rendering gives

```text
GRAPH(pi_12) = (
  (DI0,DR0,DR3),
  (DI1,DR1,DR2),
  (DT0,DR1,DI0),
  (DT1,DR0,DI1))
```

Treating the stored tuple in the reverse direction instead gives the graph
normatively assigned to alignment 16:

```text
GRAPH(pi_16) = (
  (DI0,DR0,DR2),
  (DI1,DR1,DR3),
  (DT0,DR3,DI0),
  (DT1,DR0,DI1)).
```

Thus the assertion `GRAPH(pi_12) != GRAPH(pi_16)`, together with the two bound
graphs, necessarily fails for the consistent wrong-direction implementation
that all V4 aggregates miss. The registry fixes ten ALIGN and GRAPH vectors at
indices `0,1,2,3,8,10,12,14,16,48`, all six first-occurrence CAL vectors at
indices `0,2,8,10,12,14`, both TOP goals for every fixed alignment, and both
directions of the exact twin relation `12 <-> 48`. Index 48 is included because
it is the exact `tau` twin of the direction sentinel, not because a runtime
enumerator produced it.

For a calibration whose `DI0` raw pair is `A` and whose `DI1` raw pair is its
complement `B`, the independently derived support for either goal is

```text
{(x,DI1): x in A} union {(x,DI0): x in B}, count four per pair.
```

Sorting those pairs by their global descriptor-index tuples fixes the complete
support table and its first entry fixes the chosen pair. Applying this identity
to the six ordered two-by-two partitions gives the 12 support and 12 chosen-pair
vectors in the JSON. These expectations must be copied from the governance
artifact into tests; they must not be regenerated through the GRAPH, CAL, TOP,
support, or tie-break helper under test.

## Canonical constructors and structural equality

All public projection calls pass through one fail-closed call constructor over
`(projection_id,args_tuple)`. Internal projection functions are inaccessible to
unvalidated host-language values.

Canonical objects obey all of the following rules:

1. Atoms are exact case-sensitive registered strings; subclasses, aliases,
   coercions, and normalization are forbidden.
2. An alignment is an immutable tuple of length eight in descriptor order. Its
   values are registered role atoms, type-correct at every position, and a
   bijection within each type. Equality is exact tuple equality.
3. An ingredient pair is an immutable tuple of length two with strictly
   increasing global descriptor indices. Constructors reject an unsorted pair;
   they do not sort caller input.
4. A recipe triple is exactly `(output,ingredient0,ingredient1)`. A graph is an
   immutable four-triple tuple with outputs exactly `D_out`, and is canonical
   only if structurally equal to a member of `GRAPHSET`. A calibration is an
   immutable two-triple tuple with outputs `(DI0,DI1)`, and is canonical only if
   structurally equal to a member of `CALSET`.
5. Goals are exactly `DT0` or `DT1`. A MOTIF call is compatible only when
   `cal == graph[0:2]` by structural tuple equality. Each RANDOM source graph
   must separately be structurally equal to a `GRAPHSET` member.
6. Projection results are exact immutable tuples
   `(reduced_numerator,reduced_denominator,chosen_pair,support_table)`. Support
   tables are exact tuples of `(pair,count)` entries in pair order. No caller
   input or result is normalized after construction.

The constructor validates in this exact precedence: call/value arity, runtime
tuple/type, goal literal, registered composite atoms, pair/output ordering,
alignment or CAL/GRAPH membership, RANDOM source membership, then MOTIF
compatibility. Every fixture has exactly one intended defect at the first
applicable step, so exception-code precedence is not implementer-selected.

## Closed SK08 negative registry

`golden_vectors.json` contains the complete, authoritative registry of 25
distinct calls. It is already deduplicated by structural equality of
`(projection_id,args_tuple)` and must be attempted once in listed ID order.
The population is exactly:

```text
malformed       11 = 4 call-arity + 3 value-tuple-arity + 4 wrong-type
noncanonical    12 = 2 atom + 2 order + 4 goal + 2 alignment + 2 source-graph
incompatible     2 = 2 MOTIF graph/CAL mismatches
total           25
```

A rejection counts only when `type(exc) is DomainError`, `exc.code` is the
fixture's exact code, and `exc.args == (exc.code,)`. Any acceptance, another
exception type, another code, computation before validation, mutation, report
write, filesystem/environment/cache access, or other side effect is one
mismatch. The all-pass expectation is therefore exactly 25 attempted, 25
correctly rejected, and zero mismatches. The code histogram is bound in the
JSON and sums to 25.

## Exact golden-report consequences

The JSON binds the complete nine-receipt V5 all-pass expectation, including
unchanged SK06, SK07, and SK09 receipts. The distinct fixed-vector assertion
count is 72:

```text
10 ALIGN + 10 GRAPH + 6 CAL + 20 TOP + 12 support + 12 chosen + 2 twin = 72.
```

SK08 now includes 72 bound-vector checks, 25 negative attempts, 25 exact
DomainError rejections, and zero mismatches. The successful-report object must
also add the exact aggregate vector and negative-boundary fields listed under
`golden_report_delta.add_fields` and replace the nine receipts exactly as
listed. SK09 still has six byte mutations; the mutations are applied to the
eventual V5 golden rather than the V4 object.

The complete V5 golden JCS byte length and SHA-256 are intentionally unresolved
here. Other adjudicated V5 repair streams can change the final object, and this
task authorizes only `science_repair.md` and `golden_vectors.json`, not creation
of `golden_report.json`. Assigning a final byte hash before the complete V5
object is assembled would be guessing. Integration must first merge all exact
report fields, serialize that one complete object by JCS plus one LF, then bind
its byte length and SHA-256 in the successor proposal before ratification.

## Authority boundary

Nothing here changes V4's non-headline interpretation, scope atoms, forbidden
scope, report terminality, or compute boundary. No kernel, test, provider,
model, renderer, GPU, or scientific execution was performed to derive these
governance constants.
