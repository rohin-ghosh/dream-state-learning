# FeltCraft symbolic kernel contract v4

## 1. Alignment algebra

Roles, descriptors, literal ordering, recipes, `GRAPH`, `CAL`, and `TOP` are:

```text
roles by type = [R0,R1,R2,R3] [I0,I1] [T0,T1]
descriptors by type = [DR0,DR1,DR2,DR3] [DI0,DI1] [DT0,DT1]
global descriptor order = DR0,DR1,DR2,DR3,DI0,DI1,DT0,DT1

I0 <- R0+R1
I1 <- R2+R3
T0 <- I0+R2
T1 <- I1+R0
```

An alignment is a type-preserving descriptor-to-role bijection. Enumerate the
96 alignments in nested lexicographic permutation order: raw pool, then
intermediate pool, then top pool, using only the literal list orders above.

`GRAPH(pi)` is the four descriptor-space recipe triples ordered by output
`DI0,DI1,DT0,DT1`; each ingredient pair is sorted by global descriptor order.
`CAL(pi)` is the first two triples. `TOP(pi,g)` is the pair for
`g in {DT0,DT1}`.

Let `ALIGN` be the ordered 96-tuple, `GRAPHSET` the ordered unique graphs in
first-occurrence alignment order, and `CALSET` the ordered unique calibrations
in first-occurrence alignment order. Required cardinalities are 96, 48, and 6.

## 2. Measures and exact values

MOTIF uses one uniform `pi`: source reveals `GRAPH(pi)` and target shares
`pi`. RANDOM uses independent uniform `pi_s0,pi_s1,pi_t`: two source graphs and
target calibration/goal. These are full finite products, not seed samples.

For every `c in CALSET`, the compatible target set is
`A(c)={pi in ALIGN: CAL(pi)=c}`. For each top goal, `A(c)` has 16 elements,
four distinct top pairs, and count four per pair. Consequently LOCAL and
RANDOM_SOURCE have best value 1/4; MOTIF_SCHEMA and ORACLE have value 1.
RANDOM source independence is an integer product-count identity, not a
floating-point mutual-information test.

## 3. Closed projection domains

All inputs are immutable tuples of the exact symbolic objects above. A call
outside its domain raises `DomainError` before computation and emits no report.

- `LOCAL_DOMAIN = CALSET x [DT0,DT1]`, 12 unique tuples.
- `MOTIF_DOMAIN = {(graph,cal,g): graph in GRAPHSET,
  cal=first_two(graph), g in [DT0,DT1]}`, 96 unique tuples.
- `RANDOM_DOMAIN = GRAPHSET x GRAPHSET x CALSET x [DT0,DT1]`,
  `48*48*6*2 = 27,648` unique tuples.
- `ORACLE_DOMAIN = ALIGN x [DT0,DT1]`, 192 tuples.

Every projection returns one immutable tuple:

```text
(reduced_numerator, reduced_denominator, chosen_pair, support_table)
```

`support_table` is the complete tuple of `(pair,count)` entries sorted by the
lexicographic tuple of global descriptor indices. `chosen_pair` maximizes count
and breaks ties by that same order.

LOCAL enumerates `A(cal)`. MOTIF_SCHEMA validates `cal=first_two(graph)` and
reads the requested top pair from `graph`. RANDOM_SOURCE validates both source
graphs but, by the declared product measure, enumerates `A(cal)` without using
them to change target counts. ORACLE returns `TOP(pi,g)` with support count one.

The projection module has no filesystem, environment, cache, RNG, dynamic
import, mutable global, or cross-projection object reference.

## 4. Twin and costs

`tau=(R0 R2)(R1 R3)` and fixes I0,I1,T0,T1. `TWIN(pi)` maps each descriptor to
`tau(pi(descriptor))`. Across all 96 alignments it must round-trip, change all
four graph triples, change both top actions, and preserve intermediate/top
shortest costs 5/8.

Cost algebra:

```text
raw acquisition MOVE+GATHER = 2
intermediate = two raw acquisitions + craft = 5
top = its intermediate + one raw acquisition + craft = 8
CONJ(old_top,new_top) = 16
BRIDGE(old_top,new_top) = old_top + new_top + final craft = 17
```

Old and new products are namespace-tagged immutable atoms
`OLD::DTi` and `NEW::DTj`. A bridge case is one element of
`ALIGN x ALIGN x [DT0,DT1] x [DT0,DT1]`, exactly 36,864 cases. Its required
inventory immediately before the final craft is exactly
`{OLD::old_goal:1, NEW::new_goal:1}`. The final craft consumes both and emits
`BRIDGE::B`.

SK07 tests only deletion. For every bridge case, delete the old product once
and the new product once, for exactly 73,728 checks. In either deletion state
the precondition is false, the final craft cannot emit B, and the spent
component budget leaves fewer than the 8 actions needed to recreate the
deleted top product. There is no substitution claim or substitution domain.

## 5. Runtime successful report

On all-pass only, the runner must write bytes exactly equal to the bound
`golden_report.json`. The bound file is already RFC-8785/JCS canonical UTF-8
and ends in exactly one LF. Object member order is governed only by JCS
lexicographic serialization; any presentation order in prose is nonnormative.

The validator compares raw bytes to the bound golden bytes. Six negative
fixtures are generated mechanically from the golden object and must fail:

1. remove `protocol_id`;
2. add unknown top-level key `debug`;
3. replace `protocol_id` with `wrong`;
4. replace `random_best_value` by the unreduced fraction 2/8;
5. swap the first two receipt array entries;
6. append one additional LF.

If a scientific invariant or implementation check fails, no successful report
is written and the command exits nonzero. Classification as REWORK versus
REJECT occurs in independent review, not through a second open runtime schema.

## 6. Acceptance tests

1. `SK01_DOMAIN`: 96 alignments, 48 graphs, four edges per graph.
2. `SK02_CALIBRATION`: six classes, each size 16.
3. `SK03_RANDOM`: 12 calibration-goal cases; four pairs each; count four each;
   value 1/4; integer source-factorization failures zero.
4. `SK04_MOTIF`: all 96 legal motif tuples return value 1.
5. `SK05_TWIN`: 96 round-trips; edge/top-action failures zero.
6. `SK06_COSTS`: 192 intermediate-role cases at 5, 192 top-goal cases at 8,
   CONJ 16, BRIDGE 17.
7. `SK07_BRIDGE_DELETION`: 36,864 bridge cases, 73,728 deletion checks,
   dependency failures zero.
8. `SK08_PROJECTIONS`: legal domain counts 12/96/27648/192; malformed and
   incompatible inputs raise DomainError; value failures zero.
9. `SK09_REPORT`: golden round-trip one, all six mutations rejected.
10. `SK10_SCOPE_AUDIT`: external post-implementation audit described below.

## 7. External scope audit

SK10 is not part of the runtime report and never becomes runtime input. A fresh
post-implementation reviewer writes `scope_audit.json` with exact keys:

```text
change_sha256
tracked_files
observed_imports
forbidden_matches
cli_entrypoints
passed
reviewer_interpretation_sha256
```

Arrays are sorted UTF-8 strings. `passed` is true only when:

- tracked implementation files are a subset of
  `feltcraft_symbolic_kernel/{__init__.py,kernel.py,report.py,run.py,test_kernel.py}`;
- observed imports are a subset of
  `{collections,fractions,itertools,json,pathlib,sys}`;
- the only CLI entrypoint is `python3 -I -m feltcraft_symbolic_kernel.run`;
- static AST/import/string and repository-diff audit finds no random renderer,
  life/target-agent engine, model/provider/tokenizer, DREAM/SLEEP/reader/memory,
  LoRA/weights, GPU/remote, promotion, benchmark authority, or claim path;
- `forbidden_matches` is empty;
- the fresh review binds the exact implementation and change hashes.

The audit is evidence for human review only; it is never mounted or imported by
the enumerator.

## 8. Authority

Before human approval, creating exact interpretations, critique, consensus,
and a human-authored ratification is explicitly permitted. Implementation,
tests, execution, receipts, evidence generation, compute, promotion, and claims
remain forbidden. After exact approval, authority is limited to the three
requested scope atoms in `scope_proposal.json`.
