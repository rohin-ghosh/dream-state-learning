# Stage2A fixed-protocol semantic-alias collision

Builder, September 14, 2026, 01:55 UTC. Non-material instrumentation repair,
prospective and CPU-only. No native result was inspected or rescued.

## Reproduced integration failure

Using synthetic p00/m0 CLOSED SEEK, the newly bound core and the unchanged
scanner with only `{"core": core}` as semantic metadata produce eight hits:
`PORT` at offsets254-258 and1022-1026, `STATE` at454-459 and517-522,
each in normalized and compact forms. All lie in the identical fixed system
message: `<port-id>`, `Unsupported`, `states`, and `state`. They contain no
condition-dependent data. This is a partial-core scan, not a complete inventory
test; complete metadata may expose other problems.

V3 section6.2 explicitly treats each fixed system line as shared public text.
Section8 derives aliases from private core labels and scans substrings, while
the current protocol field permits only the special STOP full-target receipt.
The combination mistakes invariant public vocabulary for private disclosure.

## Narrow repair

Permit a `semantic_alias` occurrence only when wholly inside a validated exact
protocol field at byte offset0. The field must still contain exactly the pinned
SYSTEM_MESSAGE bytes under the existing validator. Return an occurrence receipt
with that field's provenance; do not discard the hit globally. A copied protocol
at a later offset, altered protocol, appended annotation, private field, actor
message or service receives no new exemption. No PORT/STATE vocabulary allowlist
is added. Other categories, including full-target, operand, future identifier,
registered route and forbidden core, are unchanged. STOP keeps its existing
special rule; semantic-object forbidden-label checks remain binding.

This corrects evidence attribution without changing a single actor input,
training target, control, budget, held task, behavioral threshold, thesis or
provenance invariant. It does not exempt scheduled answers or future material.
Old source/receipts remain preserved and no historical result is rescored.
The repair is a new source version, not an assertion that old source passed.

Regression coverage must show receipt of constant system collisions, rejection
of all extra occurrences (including normalized/compact copies), altered/moved
protocol rejection, unchanged other-category behavior, and an actual bound
core passing this formerly failing partial integration. Whole-inventory and
native readiness remain incomplete. Formal final-paper C11 remains deferred.
