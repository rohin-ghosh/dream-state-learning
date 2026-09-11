# Multi-key writer gateway V9 — compact joint-key scout

Status: proposal only. No implementation or execution authority.

V9 supersedes the unratified V7 and V8 proposals. V7 admitted one-factor
shortcuts. V8 fixed their abstract geometry but left model-visible nuisance
crossing, oracle visibility, metric equations, and result labels open to
implementation choice. V9 resolves those items while retaining a three-file
development scout. It does not introduce the process custody or security
guard reserved for final paper-grade C11.

## Question and claim boundary

Can a rank-8 LoRA express opposite supervised native actions over a seen
eight-tool by two-mode interaction surface, rather than only a constant,
tool-only, mode-only, stratum-only, stratum-by-mode, or declared
surface-covariate habit?

This is a supervised writer-capacity test. It does not test child authorship,
lived experience, DREAM, parenting, retention, unseen-key generalization,
connected memory, continual learning, recurrence, or the whole organism.
Behavior cannot reveal the model's internal representation.

## Exact key geometry

Each of two roots contains abstract slots `t0` through `t7`. Slots `t0..t3`
are stratum `s0`; slots `t4..t7` are stratum `s1`. Orientation is attached to
slots before opaque identifiers exist:

| root | t0 | t1 | t2 | t3 | t4 | t5 | t6 | t7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| r0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| r1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 |

Opaque tool identifiers are produced later from a separately named,
manifest-bound identifier seed and assigned to slots without changing this
table. The implementation test mutates every identifier while holding slots
fixed and requires orientations to remain unchanged; the enclosing artifact
hash must change. Concrete identifiers and the identifier seed are bound only
in the later execution manifest.

For visible mode index `j` in `{0,1}`:

`W+(t,m_j) = a[b(t) XOR j]`

`W-(t,m_j) = a[1 XOR b(t) XOR j]`

Thus the maps are row-wise complements, every tool reverses across modes, and
every stratum-by-mode cell contains two `a0` and two `a1` targets. Under the
exact scored multiplicities below, deterministic constant, tool-only,
mode-only, stratum-only, and stratum-by-mode policies have best balanced
accuracy exactly `1/2`. Random mixtures cannot improve that expectation.

## Exact surface crossing

Training is the complete Cartesian product of 2 roots × 2 maps × 8 slots ×
2 modes × 8 training-template IDs. Held primary evaluation is the complete
product of 2 roots × 3 conditions (`OFF`, `W+`, `W-`) × 8 slots × 2 modes ×
4 held-template IDs. Within a root, every template ID has one literal template
with placeholders only for the opaque tool and visible mode. The same ordered
template schedule and non-key fields are used for every slot, orientation,
mode, and map. Held template literals are absent from training; root-0 and
root-1 identifiers and literal surfaces are disjoint. Root, slot, stratum,
orientation, map, template ID, row order, and request seed never appear in
ordinary model-visible text.

Training and held row order come from separately named manifest seeds that do
not consume target labels. Evaluation request seeds may depend on root, slot,
mode, and held-template ID but are identical across `OFF`, `W+`, and `W-` and
are not model-visible. CPU tests operate on the actual serialized input
multisets, require equal counts for every key and declared nuisance category,
and require every declared non-key categorical covariate, alone and crossed
with mode, to have best target accuracy exactly `1/2`. The pass claim is
limited to these tested shortcut families; identifier morphology remains a
tool identifier, not evidence of an internal mechanism.

There are eight training examples per key. Context tokens are loss-masked;
the only supervised continuation bytes are exactly `ACT: a0\n` or
`ACT: a1\n` followed by EOS. `W+` and `W-` have identical context bytes,
target byte lengths, multiplicities, row order, optimizer steps, and seeds;
only the final action label differs. Current CPU work certifies bytes and a
fake-tokenizer contract only. Under a later execution grant, a pinned real
tokenizer preflight must run before model load or fitting and require matched
candidate token counts, target masks, EOS handling, boundaries, maximum
length, and absence of truncation; mismatch is a non-reportable abort.

## Fit and request design

There are four clean-base fits: 2 roots × 2 maps. The later execution manifest
must pin Qwen2.5-7B-Instruct model and tokenizer bytes. The fixed recipe is
rank 8, alpha 16, dropout 0.05, all attention and MLP projections, learning
rate `3e-5`, two epochs, batch size 1, maximum length 2048, no packing, and no
SVD initialization.

Primary generation and primary two-candidate likelihood requests are
map-blind and receive only the held task text plus the condition's adapter or
OFF state. The explicit-map OFF oracle is a different typed request: it
receives a rendered table of the correct map and one held task, uses OFF, and
never shares a cache operation kind with a primary request. Oracle prompt
bytes, outputs, and cache records cannot enter fitting or primary requests.

Generated output parses only when its complete stripped text is exactly one
line `ACT: a0` or `ACT: a1`. Missing, malformed, fenced, truncated, multiple,
or extra-text outputs are fixed-denominator failures and are never repaired or
retried.

## Exact metrics

All primary generated metrics use the 64 held items per root and condition
(16 keys × 4 templates), each with weight `1/64`. Invalid outputs are
incorrect. For target class `c`, recall is correct class-`c` items divided by
the fixed number of class-`c` items. `BA` is the arithmetic mean of the two
recalls. Stratum accuracy is strict correct outputs divided by its fixed 32
items. `validity` is the fraction of 64 outputs that parse. Multiple ACTs are
also counted separately and must be zero.

For each prompt `x`, let `ell_c(x)` be the sum of teacher-forced token
log-probabilities for the exact full candidate continuation `ACT: a_c\n` plus
EOS. Define `q_c(x) = exp(ell_c) / (exp(ell_0)+exp(ell_1))`. Action-choice
NLL is `-log(q_target)`. Directional margin is
`ell_target - ell_opposite`. This two-candidate normalization prevents the
shared ACT prefix from supplying the action-choice gain. A missing or
non-finite likelihood record makes the run non-reportable.

For one key, NLL gain is the median across its four held templates of
`NLL_OFF - NLL_adapter`. For four values, median means the arithmetic mean of
the second and third sorted values. Adapter mean NLL gain is the arithmetic
mean of its 64 item gains. Mean-gain asymmetry is the absolute difference
between the `W+` and `W-` adapter means within a root.

For map `M`, OFF gain is `BA(adapter_M scored against M) - BA(OFF scored
against M)` using the same held items and seeds. Opposite-map BA scores the
same adapter outputs against the exact complementary labels; invalids remain
wrong. Own-minus-opposite BA is retained only as a consistency canary because
under this definition own BA ≥0.80 already implies separation ≥0.60 when
validity ≤1; it is not independent evidence.

The explicit-map oracle uses the same strict parser and fixed denominators;
oracle BA is computed identically. For each spill family, binary probability
TV per item is `0.5*(abs(q0_adapter-q0_OFF)+abs(q1_adapter-q1_OFF))`; family TV
is its fixed-item arithmetic mean. Legal-ACT rate is the fraction whose whole
output strictly parses as `a0` or `a1`; rate change is adapter minus OFF.

## Fixed panels and gates

The four spill families are: every selected tool with mode absent (8 items);
every selected tool with unsupported mode `m2` (8); every separately generated
one-character-neighbour tool with each valid mode (16); and 8 fixed unrelated
native-interface prompts. Spill prompt templates are uniform within family
and contain no target-correlated field. The unrelated interface panel has
eight frozen expected native `ACT:` outputs that are neither `a0` nor `a1`;
OFF and every adapter must score 8/8 exactly. Exact literal prompts and expected
outputs are implementation bytes reviewed before execution.

For each root:

1. `oracle_ok`: explicit-map OFF-oracle BA ≥0.90 for both maps.
2. `optimization_ok`: every key in both adapters has median action-choice NLL
   gain ≥0.50 nat, and mean-gain asymmetry ≤0.25 nat.
3. `binding_ok`: each adapter has own-map generated BA ≥0.80; stratum accuracy
   ≥0.75 in both strata; margin ≥0.50 on at least 12/16 key medians and at
   least 6/8 in each stratum; OFF gain ≥0.20; and own-minus-opposite BA ≥0.50
   as a consistency canary.
4. `interface_ok`: each adapter has validity ≥0.95 overall and ≥0.875 per
   stratum, zero multiple-ACT outputs, and 8/8 unrelated-interface accuracy.
5. `spill_ok`: for each adapter and spill family, mean binary TV ≤0.05 and
   legal-ACT-rate change ≤0.05.

All inequalities are inclusive. Values are computed from complete raw records
at full precision; display rounding never enters decisions. Both roots must
satisfy a gate for its combined predicate to be true.

## Total result classification

Missing roots, records, hashes, tokenizer preflight, stage receipts, or other
integrity/provenance requirements abort without a scientific label as
`NONREPORTABLE_ABORT`. Otherwise exactly one label is assigned in this order:

1. `ASSAY_INVALID` if combined `oracle_ok` is false.
2. `OPTIMIZATION_INCONCLUSIVE` if oracle is true and combined
   `optimization_ok` is false.
3. `INTERFACE_INVALID` if oracle and optimization are true and combined
   `interface_ok` is false.
4. `BINDING_WITH_SPILL` if oracle, optimization, interface, and combined
   `binding_ok` are true but combined `spill_ok` is false.
5. `MULTIKEY_BINDING_PASS` if all five combined gates are true.
6. `GATEWAY_NEGATIVE` otherwise.

Golden CPU fixtures cover every label, non-reportable abort, exact threshold,
immediately-below-threshold value, both-root co-failures, and pairwise
precedence. A no-learning fixture with adequate oracle but failed NLL is
`OPTIMIZATION_INCONCLUSIVE`; adequate optimization with failed binding is
`GATEWAY_NEGATIVE`.

## Bounded simple hygiene

- The run root must not exist, must resolve outside configured protected
  child, parent, CompilerGym, PCFL, and C11 roots, and must have no symlink in
  its existing parent chain. It is created exclusively; every write is
  containment-checked and fail-if-exists.
- V9 JSON is UTF-8 canonical JSON with sorted keys, compact separators, and
  exactly one trailing newline. SHA-256 binds only named V9 artifacts.
- Before fitting, one manifest binds source and launcher bytes, later-pinned
  model/tokenizer revisions, exact literals, slots, identifiers, orientation
  table, maps, corpora, row order, masks, seeds, recipe, panels, metric and
  label version, protected roots, and output root.
- Fit input is an allowlisted projection containing context, supervised
  continuation, mask, row order, seed, and recipe fields. Audit-only
  orientation/map fields, held text, oracle text, and results are absent.
- Request identity binds typed operation kind, exact model/tokenizer identity,
  adapter-tree hash or OFF, prompt and candidate bytes, seed, and all decoding
  or scoring parameters. Cache lookup revalidates the full payload. There is
  no cross-run lookup. One retry is allowed only after a preserved
  infrastructure failure produced no model output, with identical bytes and
  seed. Any model output—including invalid or truncated output—is terminal.
- Adapter trees are hashed over sorted normalized relative regular-file paths
  and bytes; links are refused. Load receipts bind the intended adapter hash or
  OFF state. Stage receipts and the final seal are fail-if-exists. The reducer
  recomputes report bytes in memory and requires the sealed report hash.
- One fresh independent implementation reviewer and a separate scientific
  advocate inspect identical source, tests, manifest, and dry-run receipts.
  Independent rejection blocks later execution authority.

Explicitly deferred to C11: process/OS isolation, adversarial filesystem and
special-file custody, generalized ancestor/threat analysis, hash-collision
semantics, interruption injection before every write, universal artifact
serialization, reusable guard infrastructure, and external release controls.

## Required current CPU evidence

1. Exact materialized counts, complements, disjointness, byte geometry,
   identifier-independent slot orientations, full nuisance crossing, equal
   weights, deterministic seeds/order, mutation failures, and exact integer
   `1/2` maxima for every named shortcut class and declared categorical
   covariate alone and crossed with mode. A positive joint orientation-by-mode
   fixture scores 1.0. Fake-tokenizer fixtures exercise the later preflight
   contract without invoking a real tokenizer.
2. Byte-exact serialized allowlists for fit, primary, oracle, and reducer
   stages; typed/disjoint oracle requests and cache identities; anti-flow
   fixtures; and the complete strict parser table.
3. Golden metric records for every equation, multi-token candidate, even
   median, invalid/missing case, aggregation level, and equality boundary;
   the total label partition; and the bounded experiment-local path, hash,
   cache, retry, adapter, receipt, seal, and reducer-replay rules above.
4. Bound fresh independent implementation and scientific-advocate reviews.

## Resources and strongest permitted statement

Implementation remains one experiment module, one focused test file, and one
thin launcher. Expected implementation plus review is 4–8 hours. Later
scientific execution is four fits under a separately ratified hard cap of 3.0
A40-hours.

The strongest permitted pass statement is:

> Across two engineered roots, target-masked rank-8 adapters expressed
> opposite supervised native-action behavior under the predeclared aggregate
> and per-stratum gates on an evaluated eight-tool by two-mode surface. All
> sixteen seen keys met the defined per-key NLL-gain threshold; directional
> margins were required on at least 12/16 keys and 6/8 per stratum, not on
> every key. The five named one-factor shortcut families and declared
> surface-covariate controls remained at chance, with no detected bound spill
> or native-interface damage.

No stronger learning, memory, mechanism, generalization, or organism claim is
licensed.
