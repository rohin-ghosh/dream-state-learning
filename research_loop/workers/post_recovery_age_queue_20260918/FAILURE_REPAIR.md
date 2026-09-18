# Preserve and repair the first diagnostic launch

The first player loaded, then failed before its first generation with
`scene_only_no_source_state`. The caller passed the full manifest scene,
including image/split metadata, to the older strict prompt contract. There were
zero generated request files. This is an operator integration error, not a child
format fault, bad caption, zero score, or evidence of learning failure.

The failed root and its source, configs, LOAD and FAILED receipts are retained.
Its own finite judge PID799961 was stopped only after verifying its unit PID,
CONFIG argument and the exact pre-generation failure. No kept life, parent,
production scorer or other process was signalled. The batch observer preserved
the terminal failure and did not restart it on observation timeout.

The repair projects only contest_id/canonical_scene, matching the existing
battery. Added an end-to-end synthetic6144-token test through the actual
contract and player feedback path. It also exposed and fixed UTF-8 canonical
hashing: both sides now use the original battery's ensure_ascii=False. A
test-only temporary-directory symlink needed canonical resolution; production
paths had already passed that check.

Attempt2 was CPU-prepared only and never dispatched. Attempt3 is a new root
with source manifest bcdd5adbcd03bc52e0ae20ca400cd6b328bc9d89aeb19a3f1d9fbae20b3e5c7b.
Eight focused/integration tests pass locally and on the receiving node;
21 inherited contract/enrollment tests pass locally and the8 pinned original
battery tests pass on the receiving node. Synthetic tests are not science data.
All original outputs, selection, budgets, model identities and claims remain
unchanged. Retrying the repaired operator protocol is declared, not hidden.
