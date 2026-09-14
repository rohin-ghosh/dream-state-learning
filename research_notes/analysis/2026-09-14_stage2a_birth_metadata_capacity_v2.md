# Measured birth metadata capacity v2

Builder, September14 2026UTC. This changes an engineering capacity only, not
the semantic object, alias ledger, public limits, matching rule or science gate.
Default birth_full_v1 remains available unchanged, including its failures.

The complete synthetic envelope was measured across64cases/512records, four
nonoverlapping eight-world CPU shards. Maxima:5870321canonical bytes,
260563nodes,200244leaves, depth8,422196distinct aliases. All except depth peak
at p29/m0/u3/CLOSED. Alias counts union complete unchanged-root ledgers and
dynamic fields; they are not whole-prefix scan results.256family-A records
exceed v1's131072leaves; none exceeds its other ceilings. No source fields
were discarded, compressed into hashes or moved to unprotected roots.

Bind explicit birth_full_v2: bytes16777216, leaves262144, nodes524288,
aliases524288, depth64. Only the leaf ceiling increases; the measured maximum
is below the next power-of-two ceiling. This is finite headroom, not a
guarantee for any future schema or arbitrary source. Overflow still fails.

Keep v1 the default so prior callers/tests and failed evidence remain truthful.
Selection of v2 must be explicit in producer, result, provenance and inventory
scan. Equivalent source metadata under both profiles must have identical bytes,
hashes and alias ledger. Capacity is independent of the optional source-occurrence
attribution repair. Native templates/held-core/allocator provenance and actual
reduced-screen qualification remain separate unfinished work.
