# Stage2A finite route basis and occurrence language v1

Builder, September 14, 2026. Prospective source-only implementation, not an
executed assay or complete material/inventory gate. Actor bytes and budgets
are unchanged; no canonical allocation, tokenizer or model was used.

## Why not enumerate every path

The complete source has off-oracle cyclic branches. Oracle suffixes omit them;
all simple paths omit revisits; arbitrary depth caps change coverage. The new
route basis stores every registered EVENT transition once, its owning query,
predicted GOT, effective WORLD destination, RECOVER, receipt and source path.
Successors use actual destinations. A registered corrective relation requires
its owning physically mismatching port. Unregistered second-recovery queries
remain unavailable. These are hypothetical source contingencies, not a claim
that the actor observed them. No goal-based or selected-oracle pruning occurs.

This is a finite transition representation, not a tuple containing serialized
automaton bytes for the old substring scanner. Every path with at least two
transitions contains an adjacent pair, but byte coverage additionally needs a
rendering recognizer. Literal `STEP p1\nSTEP p2` needles alone miss intervening
WORLD/READ records and service-field renderings. Neither a two-edge witness nor
an oracle route is by itself a complete leak detector.

## Implemented byte language

`scan_birth_route_language` reconstructs the complete selected source and its
exact retained arm binding. It recognizes:

- STEP schedules joined by registered protocol/action/service records. Each
  consecutive STEP pair is checked against the effective transition basis.
- Ordered complete registered EVENT rows, in either existing skin, within a
  contiguous typed record region. Compatible row pairs expose route fragments;
  disconnected co-occurring rows are not a path. Registered ROUTE rows can
  bridge this representation but their directory IDs are not multi-step routes.
  Mixed action/row and row/action fragments are recognized too.
- One-line ordered registered port, event or query ID lists, separated by
  spaces, arrows or commas. Query tokens denote their complete indexed rows,
  not just the task's selected row. Existing normalization also recognizes
  compact forms. No arbitrary prose or wildcard skipping joins identifiers.

Literal, ASCII uppercase/space-collapsed and compact forms use the existing
normalization. CR, NUL, Unicode and invalid types fail. Unknown text resets the
recognizer and is reported as unrecognized spans: it is outside this grammar,
not certified harmless. General English/paraphrases, escaped forms and native
chat bytes are not covered. Other existing scanner categories stay mandatory.

Finite input consumption handles cycles without a source path-depth cap or new
actor budget. Existing input, row and occurrence resource limits cause explicit
errors, never truncation followed by a clear result. This is a supplement, not
a replacement for the old explicitly supplied registered-route literal ledger.

## Occurrence custody

An action or service-row pair is receipted only if its entire causal prefix
through the second endpoint matches the retained original bytes and both
occurrences lie inside their original messages with the proper actor/service
roles. Endpoint equality alone is insufficient: changing an intervening WORLD
must invalidate the claimed recovery evidence. This admits authentic executed history and already-returned
one-step facts. Identical source text copied into a new annotation does not
inherit those offsets. ATOM cannot import CLOSED history. Bare ordered-ID route
annotations have no historical exemption. The route receipt cannot waive a
full-target, future-ID, semantic-alias or forbidden-core failure.

The source basis and grammar reports explicitly keep inventory/native/science
readiness false. Remaining integration is the complete protected metadata
schema, measured bounds, future-ID/semantic/literal/structured-route conjunction,
and held/runtime binding. A route-only clear report must not open an experiment.

## CPU evidence

- Route basis: 6 tests pass, including all64 selected birth worlds/members,
  exact effective edge coverage, both ordinary and off-oracle relation-mismatch
  contingencies, cyclic branches, unavailable recovery and off-trace mutation.
- Initial route grammar: 8 tests passed, including all512 birth decision/arm prefixes;
  injected action schedules with WORLD/READ separators, both EVENT skins,
  port/event/query list forms, lowercase/compact encodings, copied history,
  ATOM history isolation, disconnected IDs and fail-closed overflow.
- Peirce subsequently identified endpoint-only authentication as insufficient
  under a same-length intervening WORLD mutation. The implementation now binds
  the complete causal prefix. Added this regression and mixed action/row
  recognition; final rerun results are recorded separately, not inferred from
  the earlier eight-test receipt.
- Peirce's read-only basis review found no blocking branch/owner defect and
  requested explicit p25 successor coverage; that regression is now included.
  This is not independent reproduction of every receipt or scientific approval.

One initial basis test incorrectly searched for semantic state names inside an
opaque request string (StopIteration); it was repaired to use the explicit role
owner map. No production source was altered to satisfy that test.
