# S-JOIN zero-fit source/text preflight

Date: 2026-09-12 UTC  
Status: watcher-side design recommendation only. No builder source, model,
tokenizer, adapter, process, GPU job, node, or external state was changed.

## Decision

Build S-JOIN now as a pair-parameterized, zero-optimizer controller. It may run
speculatively beside W0, but it must import the sealed W0 action-surface
specification and may become fit-eligible only if a later independent carrier
receipt qualifies that **same specification hash**. S code and S manifests use
`action_slot in {0,1}` and never contain native action literals of their own.

This separates three predicates which must not be collapsed:

```text
PAIR_SPEC_BOUND
  = S imported one pre-output W0 action-surface specification

PAIR_CARRIER_OK
  = an independent generation-plus-score carrier qualified that exact hash

W0_WRITER_OK
  = the four-fit W0 run sealed/replayed MULTIKEY_BINDING_PASS
```

`PAIR_SPEC_BOUND` is enough for speculative source acquisition and text-only
reads. `PAIR_CARRIER_OK` can promote a passing zero-fit result without rerunning
it. `W0_WRITER_OK` is additionally required before either S LoRA fit. If the
carrier fails or qualifies different bytes, the speculative S roots are burned;
they cannot be rebound, renamed, or reused with another pair.

The existing “one root” plus “wrong-root must pass before fitting” wording is
not jointly executable. The smallest complete zero-fit unit is therefore two
predeclared source roots: primary `r0` and disjoint mate `r1`. This permits a
real cyclic wrong-root mount. Only `r0` is eligible for the first paired LoRA
kill gate; acquiring `r1` early neither releases its fit nor permits selecting
it when `r0` fails. A third root remains downstream of a qualifying `r0` fit.

## Sealed inputs and stage order

Before any child/model output, seal one manifest containing:

- the content hash of the imported W0 action-surface specification, including
  the ordered canonical post-`ACT:` bytes, complete response continuations,
  parser, backend registry, base revision, tokenizer and chat template;
- two ordered roots, eight fresh opaque situation keys per root, exactly four
  hidden orientation bits of each value per root, all actor/evaluation seeds,
  opportunity order, action-display order, renderer literals and row order;
- two opaque public outcome continuations chosen before inference as the first
  tokenizer-valid equal-length pair (ordered `i,j`, then lexical) from the
  closed list `OBS: dax`, `OBS: wug`, `OBS: blick`, `OBS: koba`, each with one
  final LF and EOS; no fallback string may be added in this version;
- the within-situation donor permutation below, text-store schema, retrieval
  policy, request order, generation/scoring parameters, thresholds and labels;
  and
- explicit disjointness sets against every W0 key, form, request/cache kind,
  source root, adapter and development diagnostic.

The controller order is fixed:

```text
STATIC -> SOURCE -> SEAL_LEDGER -> DERIVE -> THEOREM -> GOLD_EQ_TEXT
       -> TEXT_READS -> REDUCE -> SEAL
```

It must have no trainer/optimizer dispatch edge. Every terminal record asserts
`optimizer_steps == 0`, no adapter input/output and no training cache kind.
Static construction can run before W0 starts. The remaining stages may use the
imported prospective pair while W0 runs; until `PAIR_CARRIER_OK` arrives their
strongest label is `S_ZERO_FIT_PROVISIONAL`.

## Authoritative source, not child narration

For each root and each situation, run a fixed 16 opportunities in a
predeclared interleaving. Do not stop early after coverage. The child sees only:

- the opaque situation;
- the two imported legal action lines, with display order balanced eight/eight
  over the 16 opportunities;
- its prior public trials for that situation; and
- a generic instruction to choose one action and explore, never an action
  prescription, goal value, reward, correctness bit or hidden orientation.

The deterministic public law is

```text
outcome_slot = action_slot XOR orientation[situation].
```

The environment accepts only an exact imported action, emits the canonical
public outcome, records it in its own ledger and exposes that response to the
child. There is no final-answer/revision turn and no success selection.

An authoritative event is a mechanical one-to-one join, on a fresh event
nonce, of:

```text
child request hash
+ raw child-output hash
+ the one strict parsed ACT span and canonical action bytes
+ engine input/action hash
+ engine public-response bytes/hash
+ root, situation, opportunity and engine replay identity.
```

The join is invalid unless the parsed child action equals the engine input,
the environment response is causally later, both sides name exactly one nonce,
and deterministic engine replay reproduces the public outcome. Raw child prose
is preserved in the audit projection but is not read by admission, the event
renderer, the text store or any later fit. NOTE/REVIEW/DREAM/PREDICT text and a
child's paraphrase of the result are never source fields.

For each `(root, situation, action_slot)`, admit exactly the first two joined
valid events in source chronology. Preserve every invalid, rejected and extra
attempt. Each root must therefore have exactly 32 admitted events:

```text
8 situations x 2 actions x 2 occurrences.
```

No top-up, forced action, evaluator action, synthetic event or root replacement
is allowed. Coverage is valid only when every situation has two admitted events
per action, both authoritative public outcomes, and the declared 4/4
orientation split.

## TRUE and within-situation OUTCOME_SHUFFLED

Seal the source ledger before deriving a branch. In a situation, index admitted
events as `e[a,j]`, where `a` is action slot and `j` is admitted occurrence.
TRUE uses each event's own environment outcome. SHUFFLED uses the fixed
derangement

```text
recipient e[a,j] <- donor e[a XOR j, 1-j].outcome
```

Thus every donor is used exactly once, no event donates to itself, and each
action receives one outcome of each kind. Only the bound outcome bytes/hash and
external donor reference may differ. Donor identity is never model-visible.

For every admitted event, render exactly two registered forward and two
registered inverse training rows (128 rows per root/branch), and freeze four
train-disjoint held forms per direction:

```text
forward input:  situation + executed imported action
forward target: branch-bound outcome (own public outcome in TRUE; donor in SHUFFLED)

inverse input:  situation + desired branch-bound outcome
inverse target: exact imported ACT continuation
```

The renderer is a reversible field projection. It may not infer a lesson,
better action, correctness, policy or replacement target. Event IDs,
orientation, admission status, donor identity, occurrence, chronology and
report labels stay outside encoded text.

SHUFFLED rows and stores are explicitly synthetic controls. They are never
described as authoritative child events even though every non-outcome field is
inherited from the authoritative ledger.

TRUE and SHUFFLED must have identical event IDs, action fields, row count,
renderer allocation, corpus order, masks, EOS count and target positions.
Their action- and outcome-target multisets must match globally and separately
by root, situation, direction, renderer and orientation stratum. Prompt and
supervised token totals must match. Inherited action continuations need not
have equal lengths; report both lengths and preserve their exact multisets.
No **pre-response** byte length, token length, padding, target-start offset,
candidate order or suffix may predict the target above `.50`.

## Deterministic construction and shortcut theorem

Before a model read, fail closed unless enumeration over the sealed source,
train and held tables proves all of the following exactly:

1. the engine oracle and joined-event replay are `1.0` on every admitted row;
2. TRUE's `situation x action` forward oracle and `situation x outcome`
   inverse oracle are `1.0`;
3. both joint oracles are exactly `.50` in SHUFFLED;
4. constant, situation-only, action-only, outcome-only, renderer-only,
   occurrence-only, source-order-only and action-display-order-only policies
   have balanced accuracy exactly `.50` in both branches/directions;
5. every predeclared pair of model-visible nuisance fields which omits the
   necessary joint relation has Bayes-optimal balanced accuracy `.50`;
6. targets balance exactly by every partition named above, and SHUFFLED has
   `P(outcome | situation, action)=.5` for both actions in every situation;
7. raw-byte and token scans find no orientation, answer row, correctness,
   reward, admission bit, donor/event identity, W0 key/form, historical
   compiler prose, report label or model-visible clock/run ID; and
8. changing only the desired outcome redirects the symbolic TRUE inverse
   answer on all 16 `(root,situation)` coordinates, while cyclic wrong-root,
   new-situation and necessary-row-deletion fixtures have their declared
   chance/no-evidence values.

Also prove exact candidate masks through LF+EOS, no target-boundary-straddling
token, loss-mask complementarity, fixed four-row packing, and byte-identical
TRUE/SHUFFLED structure after replacing outcome tokens with slot indices.

## Exact GOLD/TEXT preflight

For a query, GOLD projects all four branch rows for its situation in one fixed
target-blind order. TEXT appends each TRUE canonical event, or each separately
typed SHUFFLED derivative, exactly once to an isolated root/branch store and
retrieves on **situation only**; action, desired outcome, answer candidate and
target never enter retrieval. A retrieval passes only if its external receipt
cites exactly the four source event IDs/hashes (and donor references for
SHUFFLED) and its model-visible bytes are identical to GOLD. The actor block
contains compact predeclared citation IDs but no hashes/envelopes; the external
receipt binds each citation to its authoritative event hash. Citation bytes
must themselves pass the nuisance-balance theorem. Consequently one clean-base
request panel can serve both GOLD and TEXT after `GOLD_EQ_TEXT` is proven.

Reserve a 256-token memory partition after public task/state and before child
history; reserve generation first, and never evict or truncate task/state. All
four complete event rows plus citations must fit. Pad target-independently to
the exact partition length. OFF uses a presealed neutral sham block with the
same wrapper, position and token count, plus one separately reported native-
empty sensitivity. If sham versus native-empty changes value or legal syntax
by more than `.05`, the carrier comparison is invalid.

Run strict generation and full-continuation candidate scoring on all four held
forms: 64 inverse and 64 forward requests per root/branch. Every held label is
the sealed TRUE engine-law answer; SHUFFLED changes the evidence block, never
the evaluation answer. Run OFF queries that are byte-identical outside the
memory partition and carry the neutral block in that same partition. Invalid,
multiple or truncated outputs score wrong. Reducer replay means recomputing
from sealed raw requests/outputs; it does not assume GPU decoding is byte-
reproducible.

The frozen denominator is 2,688 typed model requests: per root, 768 core
requests (`TRUE`, `SHUFFLED`, and sham-OFF x 128 items x generation/score), 256
native-empty sensitivity requests, 256 TRUE necessary-row-deletion requests,
and 64 requests for the 32 one-form new-situation items. Cyclic wrong-root and
store-miss requests render byte-identically to an already executed sham-OFF
item and reuse that raw record; they do not create duplicate model calls. The
unrelated eight-action copy result is inherited from the exact pair-carrier
receipt rather than rerun or reselected by S. Use separate clean-base workers
and disjoint caches for every root/condition/modality; no adapter is ever
loaded. Hard-stop result-blind at 2.0 A40-hours at the next request boundary
and label an incomplete panel `S_RESOURCE_INCOMPLETE`.

The zero-fit text assay passes only if, separately for both roots:

- TRUE strict-generation BA and candidate-choice BA are each at least `.90`
  in both directions;
- TRUE minus SHUFFLED is at least `.20` for both modalities and directions,
  and TRUE minus OFF is at least `.20`;
- inverse legal-action and forward legal-outcome validity are each at least
  `.95`, with zero truncations and zero multiple responses;
- swapping only desired outcome redirects inverse generation and candidate
  argmax on at least 29/32 held-form pairs;
- deleting the two records for the necessary action family lowers forward and
  inverse value by at least `.20` rather than being rescued by a prior;
- cyclically mounting the other root's store, querying a new situation, or
  querying an unrelated interface item retrieves zero rows, yields the exact
  OFF prompt-token IDs, and therefore has zero retrieval-induced candidate TV
  and zero legal-response-rate change;
- the fixed unrelated-native-action copy panel remains 8/8 for the clean base;
  and
- packing, citations, cache namespaces, request completeness, model/tokenizer
  identity, resource ceiling, raw seal and reducer replay all pass.

The deterministic symbolic reader counts the two rows for the supplied input,
emits their unanimous bound value, and emits slot zero on an exact tie. Against
the TRUE held labels it must therefore score TRUE `1.0` and SHUFFLED `.50` in
both directions. A symbolic pass cannot rescue a neural TEXT failure.

## Stop gates and labels

Precedence is exact:

1. bad/unresolved pair-spec hash, registry/parser/tokenizer mismatch, or any
   pre-output freeze/disjointness failure -> `S_NOT_RUN`;
2. join, provenance, coverage, engine replay or 32-event geometry failure in
   either predeclared root -> `S_SOURCE_INVALID`; preserve both roots and do
   not replace the failed one;
3. donor, balance, token geometry, theorem, leakage, cache or GOLD-equals-TEXT
   failure -> `S_CONSTRUCTION_INVALID`; make no text-model request;
4. symbolic oracle failure, neural GOLD/TEXT threshold failure, citation,
   packing, deletion, redirection, wrong-root, interface or reducer-replay
   failure -> `S_ASSAY_INVALID`;
5. request-count/resource-cap failure -> `S_RESOURCE_INCOMPLETE`;
6. all zero-fit gates pass while the independent
   `SEMANTIC_EXACT_ROW_CARRIER_OK` receipt is pending ->
   `S_ZERO_FIT_PROVISIONAL`;
7. carrier failure or a qualified receipt with a different surface hash ->
   `S_PAIR_UNQUALIFIED`; roots are burned for future pair versions;
8. all zero-fit gates pass and the exact imported surface later receives
   `SEMANTIC_EXACT_ROW_CARRIER_OK` (`PAIR_CARRIER_OK`) ->
   `S_ZERO_FIT_READY_W0_PENDING`;
9. only the conjunction of `S_ZERO_FIT_READY_W0_PENDING`, exact pair-hash
   equality and a sealed/replayed `W0_WRITER_OK` can release the two `r0`
   TRUE/SHUFFLED LoRA fits.

If a terminal carrier failure arrives during speculative S execution, finish
only the in-flight request, issue no next request, seal partial evidence and
apply rule 7. This stop signal cannot kill or mutate W0 or any unrelated job.

No source/text observation may change roots, pair, outcome strings, prompts,
forms, donors, row order, thresholds, parser, retrieval, fit recipe or which
root is primary. A change creates a new version with new source identities.

## Contamination boundary and meaning

W0 may export only its sealed action-surface specification and independent
qualification receipt to S; it may not consume S prompts, outputs or outcomes.
S consumes no W0 row, key, adapter or diagnostic output. TRUE and SHUFFLED
stores, model reads and all later adapters are quarantined from nursery,
parent, paper-child and final CompilerGym ancestry. SHUFFLED is never a child
experience or deployable memory. Text-read outputs never return to the source
ledger or any training corpus.

A zero-fit pass establishes only that authoritative child actions can be
joined to public environment outcomes without narration, that the proposed
corruption destroys only their conditional binding, and that the exact-text
reader exposes the intended relation through the inherited action surface. It
is not evidence of LoRA writing, retention, autonomous reflection, discovery,
generalization, parenting, connected knowledge or lifetime improvement.
