# FeltCraft symbolic kernel contract v3

## 1. Closed domains

The registered roles and recipes are:

```text
raw:          R0 R1 R2 R3
intermediate: I0 I1
top:          T0 T1

I0 <- R0 + R1
I1 <- R2 + R3
T0 <- I0 + R2
T1 <- I1 + R0
```

Public descriptor symbols are `DR0..DR3`, `DI0..DI1`, and `DT0..DT1`.
An alignment `pi` is a bijection from descriptors to roles within each type.

Enumeration order is lexicographic nested order over:

1. permutations of `[R0,R1,R2,R3]` assigned to `[DR0,DR1,DR2,DR3]`;
2. permutations of `[I0,I1]` assigned to `[DI0,DI1]`;
3. permutations of `[T0,T1]` assigned to `[DT0,DT1]`.

Python/JSON/string collation is not normative. The literal list orders above
are. There are exactly `4!*2!*2!=96` alignments, indexed `0..95` in that nested
order.

For an alignment `pi`, `GRAPH(pi)` is the four recipe triples rendered in
descriptor symbols, ordered by output descriptor in
`[DI0,DI1,DT0,DT1]`; ingredient descriptors are sorted by the literal global
descriptor order
`[DR0,DR1,DR2,DR3,DI0,DI1,DT0,DT1]`.

`CAL(pi)` is the first two intermediate triples of `GRAPH(pi)`.
`TOP(pi,g)` is the ingredient pair for top goal descriptor
`g in [DT0,DT1]`.

## 2. Exact regime measures

The probability spaces are uniform finite products, not realized seed sets.

For MOTIF, source observations contain `GRAPH(pi)` for one `pi`, and the fresh
target instance has the same `pi`.

For RANDOM, two complete source observations contain
`GRAPH(pi_s0), GRAPH(pi_s1)` and the fresh target uses `pi_t`, where
`pi_s0`, `pi_s1`, and `pi_t` are independent uniform elements of the 96-set.

Every posterior conditions on the literal symbolic observations it receives.
There are no nuisance bytes, identifiers, selection event, rejected decks, or
hidden empirical seed mapping. The accepted event is definitionally the whole
closed domain.

For every target calibration `c=CAL(pi_t)` and top goal `g`, enumerate all
`pi` satisfying `CAL(pi)=c` and count `TOP(pi,g)` exactly.

Required golden facts:

- every calibration equivalence class has size 16;
- for each `g`, exactly four distinct ingredient pairs occur;
- each pair occurs exactly four times;
- `max_a P(TOP=a | CAL=c,g,RANDOM)=1/4`;
- source graphs have exactly zero conditional mutual information with
  `TOP(pi_t,g)` under RANDOM because the product measure factorizes;
- in MOTIF, the observed source `GRAPH(pi)` makes `TOP(pi,g)` a point mass.

Mutual-information equality is proved by integer count factorization; no
floating-point logarithm is an acceptance test.

## 3. Twin transform

```text
tau = (R0 R2)(R1 R3)
tau fixes I0,I1,T0,T1
```

`TWIN(pi)` maps each descriptor to `tau(pi(descriptor))`. Required facts over
all 96 alignments:

- `TWIN(TWIN(pi))=pi`;
- all four recipe triples differ between `GRAPH(pi)` and `GRAPH(TWIN(pi))`;
- intermediate shortest action lengths remain 5;
- top shortest action lengths remain 8;
- `TOP(pi,g) != TOP(TWIN(pi),g)` for both top goal descriptors.

This establishes an authentic-content counterfactual only.

## 4. Symbolic action plans

The action-cost grammar is algebraic; no environment is executed in v3:

- acquiring a raw ingredient costs `MOVE+GATHER = 2`;
- crafting an intermediate costs one action after its two raws;
- crafting a top costs one action after its intermediate and additional raw;
- crafting a bridge costs one action after its two top products.

Thus every intermediate has shortest cost 5 and every top has shortest cost 8.

`CONJ(old_g,new_g)` is two independent top goals and has cost 16. It is labeled
conjunctive retention, not composition.

`BRIDGE(old_g,new_g)` has the public final relation
`B <- old_g + new_g`. Its shortest cost is 17, and the final action consumes
the two separately produced top outputs. For every alignment pair, deleting or
substituting either component plan makes the bridge impossible within budget.
This is the registered causal old→new join for the later rendered benchmark.

## 5. Exact symbolic projections

- `LOCAL(c,g)`: receives only target calibration `c` and goal `g`.
- `MOTIF_SCHEMA(graph,c,g)`: receives a source `graph`, plus target `c,g`,
  under the declared persistent regime.
- `RANDOM_SOURCE(graph0,graph1,c,g)`: receives two complete independent source
  graphs plus target `c,g` under the declared independent regime.
- `ORACLE(pi_t,g)`: receives target alignment; scorer-only.

Each is a pure function over immutable tuples. It has no filesystem,
environment, cache, RNG, global, import, or object reference to another
projection.

Required values for every legal input:

```text
LOCAL best success = 1/4
MOTIF_SCHEMA best success = 1
RANDOM_SOURCE best success = 1/4
ORACLE success = 1
```

Ties choose the ingredient pair whose descriptor-index tuple is smallest in
the literal global order. A symbolic projection returns an exact numerator,
denominator, chosen pair, and the complete sorted support-count table.

## 6. Closed report schema

The only output is one canonical JSON object with these keys in this semantic
order:

```text
protocol_id
alignment_count
calibration_class_histogram
random_support_count_histogram
random_best_value
motif_best_value
twin_roundtrip_failures
twin_edge_change_failures
twin_top_action_change_failures
intermediate_cost_histogram
top_cost_histogram
conjunctive_cost
bridge_cost
bridge_dependency_failures
test_receipts
verdict
```

`random_best_value` and `motif_best_value` are reduced integer
`{numerator,denominator}` records. Histograms are ordered arrays of
`{key,count}` rather than maps. `test_receipts` is ordered by the acceptance
test order below and contains only `{test_id,passed,observed}`. No hidden
alignment, answer table, successful plan, traceback, path, timestamp, host
metadata, or free-form debug field is permitted.

Canonical output is RFC-8785/JCS UTF-8 with exactly one trailing LF. This
serializer affects only the receipt, not any posterior or scientific value.

## 7. Acceptance tests and verdict

In order:

1. `SK01_DOMAIN`: exactly 96 unique alignments and four graph edges each.
2. `SK02_CALIBRATION`: all calibration classes size 16.
3. `SK03_RANDOM`: four equiprobable top pairs and value 1/4 for every class and
   goal; integer factorization proves source independence.
4. `SK04_MOTIF`: source graph gives value 1 for every alignment and goal.
5. `SK05_TWIN`: involution, all-edge change, top-action change, and equal costs
   for every alignment.
6. `SK06_COSTS`: intermediate=5, top=8, CONJ=16, BRIDGE=17.
7. `SK07_BRIDGE`: both old and new products are necessary for every alignment
   pair; deleting/substituting either fails within budget.
8. `SK08_PROJECTIONS`: exact input signatures and values match section 5.
9. `SK09_REPORT`: schema rejects unknown/missing keys and canonical round-trip
   is byte-identical.
10. `SK10_SCOPE`: source/import/CLI audit finds no random renderer, life engine,
    model/provider/tokenizer, DREAM/SLEEP/reader, LoRA/weights, GPU/remote, or
    promotion entry point.

Any missing receipt, exception, resource exhaustion, nondeterminism, or failed
test yields `REWORK`. A mechanically complete run with a falsified scientific
invariant yields `REJECT`. Only all ten passes yield `RETAIN_SYMBOLIC_KERNEL`.

That verdict permits no scientific claim and no automatic next stage.
