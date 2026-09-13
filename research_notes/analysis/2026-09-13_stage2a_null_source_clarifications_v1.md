# Stage2A null source clarifications v1

Builder decision, September 13, 2026, 21:54 UTC. These bind routine source
details prospectively, under Rohin's standing authorization, before controller
material, model outcomes, or null scores. They add no human approval gate and
do not implement the final-paper C11 guard. Existing protocol controls and
scientific claims are unchanged.

Parent Stage2A-v4 SHA256:
`ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1`.
The earlier Builder clarification remains unchanged at SHA256
`5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9`.

## Exact NPAIR names

In v2 section 11.1's NPAIR preimage, `name_Na` and `name_Nb` are exactly these
ASCII descriptive names, ordered by the associated numeric N index:

```text
N0 sentinel_first
N1 display_first
N2 display_last
N3 lexical_first
N4 lexical_last
N5 shortest_first
N6 goal_digest
N7 current_digest
N8 character_columns
```

The bytes contain the descriptive token only, not `N0`, a space, or the whole
display line. Always order the two names by their N0..N8 index even when the
API receives them in reverse. Keep every separator, candidate action byte,
rank-sum/max field, and SHA256 comparison exactly as v2 specifies. No salt,
master, outcome, alternative spelling, or name-selection search is allowed.
Check all 36 pairs in both API orders and exact preimage bytes.

## S_READ_ALL12 goal arrival

After its required true public match/mismatch THINK receives ACK, this actor
emits STOP if latest public CURRENT equals task GOAL. If not at GOAL, it
continues the specified RECOVER-after-mismatch or new-INDEX-after-match path.
It does not skip CHECK, stop on predicted GOT, or consult an evaluator.
Its initial INDEX, relation scan order, READ budget, no-candidate termination,
and all other schedule rules are unchanged. The other five fixed-step actors
retain their prescribed STOP counts; do not improve them with this predicate.

Required tests cover reached/matched, reached/unexpected, unresolved/matched,
unresolved/mismatch, and malformed/cap states. Model execution and whole-chain
scoring remain separate, unperformed work.

## Query READ-CHECK is outside the registered null panel

All held CHECK intervention members in v2 section 9 and v3 section 5 are STEP
outcomes on an implicated EVENT. Thus their KEEP and REVISE operands are legal
under the unchanged actor grammar. Birth READ-CHECK targets that revise a query
are not among these 64 held null-panel members.

Do not add `THINK KEEP <query>` or substitute an invented EVENT. The bounded
one-turn null API rejects a query-implicated CHECK as unsupported. This is not
a missing required member or a reason to hold the defined event-CHECK panels.
Any later expansion to query-CHECK nulls needs its own explicit specification.

## Limits

These bindings are not favorable null results. Every singleton/pair and
autonomous schedule still has to execute on the bound held cases and meet its
unchanged caps, with all failed outcomes retained. Do not reseed, reorder,
weaken the actors, or tune these choices after inspecting their scores.
