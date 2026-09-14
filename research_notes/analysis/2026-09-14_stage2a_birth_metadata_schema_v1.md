# Stage2A complete birth metadata schema v1

Builder, September14 2026, prospective CPU source binding. No canonical roots,
models, tokenizers or outcome-conditioned choice. This fills Builder-owned
schema definitions, not a new human approval or final-paper C11 gate.

## Complete private representation

The semantic object has the existing twelve protected roots. Keep underlying
values, not merely integrity hashes. No private label moves to an unprotected
root to avoid scanning. Encode tuples as JSON arrays and preserve null distinctly.

| Root | Bound source contents |
|---|---|
| case_id | world_id and member_id from the complete reconstructed case |
| causal_pair_id | domain, world_id and pair_type; not a target/unit identifier |
| core | Exact bound retained-arm core object, unchanged |
| evaluator | Expected target action, task START/GOAL/CURRENT, selected effective outcome, physical and semantic depth |
| factors | Every descriptor field/property, including world_id/member_id, case identity, family_bit and relation_slot |
| future | Complete candidates, disclosed IDs, future IDs, candidate source paths and retained disclosure receipts from the existing future producer |
| mutation | Full selected construction's effective-vs-predicted mismatches and explicit relation-swap provenance/typed before-after fields for the paired construction; not merely a changed hash |
| oracle | Entire original trace, all facts and all four expected targets, complete registered services and effective world edges, original task, complete route-transition basis with recovery ownership |
| recovery_match_id | Exact descriptor tuple encoded as array, or null |
| role_keys | All reconstructed role-key/token bindings; no selected-path filtering |
| target | Exact target unit plus corresponding BirthTarget, current arm and exact retained boundary/indices |
| unit_id | Exact shared supervised unit identity |

Metadata remains evaluator-only. Original omitted history never enters the
arm's public graph or actor prefix. Source provenance binds constructor, master,
role, case and record hashes separately; it is not a substitute for these roots.

## Faithful structured encoding, not text concatenation

Encode each action losslessly as parsed command/verb/operand, with the original
byte SHA and an exact re-render check. Do not concatenate a private original
trace into one raw scalar and misclassify authentic earlier actor turns as
newly disclosed scheduled answers. The target includes exact current target
bytes plus its parsed fields; all original trace/target bytes must re-render
exactly from their structured representations. This does not remove any command,
operand, record, ordering, response, outcome or source metadata.

Encode service rows with the actual uppercase wire field names: EVENT, AT,
FOR, DID, GOT, RECOVER, EVIDENCE; or ROUTE, AT, FOR, QUERY. WORLD/task fields
likewise use CURRENT/START/GOAL. This preserves the protocol's declared shared
vocabulary rather than inventing private aliases for ordinary wire syntax.
Keep field order via the declared skin and check exact raw registry re-rendering.
Represent raw read requests as action records, not dictionary keys containing
whole scheduled actions. Represent effective edges as ordered typed AT/DID/
CURRENT records. Keep all rows, including off-trace and mismatching branches.

For descriptor identities only, map dataclass world/member names explicitly to
world_id/member_id. Other descriptor names remain unchanged. These schema names
are chosen before any full-object scanner outcome; they cannot be retuned to
make a failed source pass. New collisions require diagnosis, not silent omission.

Original raw construction/trace/record bytes remain available in the immutable
reconstructed source snapshot and bound integrity receipt. Structured semantic
encoding must round-trip them where applicable; hashes alone are insufficient.
Any unsupported field/type, missing target/row or unaccounted construction
surface must fail rather than be silently ignored.

## Bounds and tests

The legacy scanner profile stays unchanged for existing callers. Add a separately
named `birth_full_v1` semantic-only resource profile: 16MiB canonical semantic
bytes,131072 leaves,524288 nodes,524288 unique aliases, depth64. Public prefix,
target, field and hit bounds stay unchanged. These are initial hard engineering
ceilings, not proof of the actual schema envelope; measure counts/bytes/aliases
over the complete synthetic birth envelope and report maxima before promotion.
Never truncate or drop source fields. Overflow remains an explicit failure.

Test complete field/row/target/future coverage, exact re-rendering, off-trace
mutation rejection, tuple/null semantics, per-arm retention isolation, family/
recovery variants, deterministic bytes, source alias derivation and measured
bounds. A complete metadata object still does not qualify held-core, native
templates, materialization, training, or scientific claims. Combine semantic,
future, literal and structured-route checks; no category may waive another.
