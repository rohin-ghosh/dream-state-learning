# Main metadata-read budget amendment — September 17, 2026

This explicitly supplements `FLEET_MAIN_SOURCE_SCOPE_20260917.md`; it does
not mutate the registered generation1 plan or reuse any consumed operation.

Bernoulli's stat-only receipts show 12 of 13 completed journal prefixes exceed
320 MiB. Those 13 prefixes total 5,422,533,335 bytes before node5, future
records or repeat verification. The old per-life example is not executable
coverage. Evidence: `r167_legacy_custody_20260917/EUCLID_HANDOFF.md` and its
bound per-node `*_TRAIN_STAT.json` receipts.

Main authorizes a **new, explicitly labeled immutable generation** for the
same 21 life/root identities in generation1 (SHA256
`5d73091fa467d24ec595f7f6adce8ce9f99e07d1569d2a97795302702e003b97`):

- Increase the aggregate TRAIN metadata read ceiling from 8 GiB to **16 GiB**.
- Keep the adapter-only read/copy ceiling at **16 GiB**; at most 2 GiB per
  life per kind. Allocate per-life limits from actual sizes plus bounded
  three-sleep headroom; their sums must not exceed the aggregate ceilings.
- Preserve all prior plans, reads, charges and failures. This is a larger
  declared ceiling, not a reset or a hidden source-read bypass.
- Keep the exact three prompts, original birth/system text, ON/OFF conditions,
  initial plus next-three-sleep schedule, 504-call /258,048-generation-token
  ceilings, node2 physical0/1 restriction and September17 15:30UTC /08:30PDT
  deadline. Freeze fresh actual identity/frontier references before outputs.
- Bind historical birth references only where authenticated by INITIAL
  history, preserving separate current PLAN/GUARD custody. No text rewriting
  or false equivalence between different PLAN files.
- All original visibility, source-read, private-copy, no-learner-write,
  no-signal, no-credential-change and no-lease-change restrictions remain.

Euclid may persist exact per-life source-read/copy authorities under this
scope after CPU/provenance checks. GPU execution still needs its separate
bounded admission/GO; missing lives do not block eligible fixed cells or
become negative scores. No benchmark outcome or learning claim follows
from this operational resource amendment.
