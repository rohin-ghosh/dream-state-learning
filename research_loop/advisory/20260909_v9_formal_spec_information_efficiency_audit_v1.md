# V9 formal-spec information-efficiency audit v1

Date: 2026-09-09

Status: read-only size/structure audit. This note does not alter V8, the V9
draft, their bound hashes, architecture, acceptance obligations, or authority.
It proposes no implementation or execution.

## Measured artifact surface

The V8 architecture-change JSON is `161,345,175` bytes (about 154 MiB). Its
main multiplicative surface is:

- `9,443` information items;
- `45` stages;
- `424,935` explicit visibility cells;
- `126` acceptance tests;
- `15` graph nodes, `12` graph edges, `8` loops, and `6` claim deltas.

The change directory is about 154 MiB; the consensus is about 152 KiB and the
V9 repair draft about 9 KiB. The scientific architecture itself remains three
functions; almost all byte growth is an expanded laboratory visibility and
receipt representation.

## Verdict

The explicit projection may be useful as a mechanically checkable derived
artifact, but it is not an information-efficient normative source for repeated
human/model deliberation. Sending, parsing, comparing, and re-ratifying 154 MiB
for every repair consumes attention without adding corresponding scientific
resolution. It also makes exact human review largely nominal.

V9's own R12 points toward the repair: one normative deterministic projection.
The missing distinction is between:

1. **compact normative source:** canonical object families, channel defaults,
   exceptions, phase rules, schemas, graph edges, and generator algorithm;
2. **derived exhaustive projection:** all concrete objects/cells produced
   deterministically from that source; and
3. **equality receipt:** independent builders reproduce the exact projection
   hash and fail on any discrepancy.

Human ratification and independent interpretation should bind the complete
compact source bytes, generator bytes, schema bytes, expected counts, and
expected derived root. The full projection remains available for automated
closure checks but need not be the prose-level deliberation substrate.

## Requirements that cannot be compressed away

- Per-channel access is independent; value access never implies timing, cache,
  retry, or error access.
- Defaults remain fail-closed.
- Every exception is explicit and source-located.
- Every canonical object and phase-constructible evidence family is generated.
- Independent builders match object IDs, stage IDs, cells, schemas, graph,
  loops, claims, counts, ordering, and final digest exactly.
- Mutation tests show that missing objects, changed defaults, alias
  substitutions, stage shifts, and omitted exceptions change the root or fail.
- The derived artifact is never treated as evidence that future runtime rows
  exist or passed.

## Information-per-token recommendation

Before a V9 interpretation round, measure whether the compact normative source
can reproduce the current intended projection. If it cannot, the compact
language is incomplete. If it can, use the compact source plus equality
receipts as the reviewed object and retain the 154 MiB expansion as a derived
audit artifact.

This changes representation efficiency, not scientific obligations or the
THINK/DREAM/SLEEP architecture. Adoption would still be a material systems
choice requiring the full `AGENTS.md` path.
