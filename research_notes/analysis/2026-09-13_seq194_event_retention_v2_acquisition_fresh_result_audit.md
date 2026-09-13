# SEQ-194 / EVENT-retention-v2 acquisition: fresh result audit

**Date:** 2026-09-13 PT  
**Audited run:**
`/localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_acquisition_20260913_attempt5`
on node 2  
**Scope:** read-only audit of the terminal native artifacts. I did not invoke a
model or tokenizer, fit or mount an adapter, use a GPU, or modify Astra-owned
source or artifacts.

## Verdict

**PASS the predeclared A200 writer-acquisition prerequisite, narrowly.**

For each of learner/optimizer seeds 0, 1, and 2, the frozen base failed every
read, while the independently fitted A200 adapter exactly emitted all four
trained-bank EVENT rows at both the W0 diagnostic surface and the W8 exposed
DEV paraphrase. It emitted none of the four untrained-bank rows. Every response
ended normally; there were zero readout truncations. The raw result is:

| learner seed | surface | C0 A | C0 B | A200 A | A200 B |
|---:|---|---:|---:|---:|---:|
| 0 | W0 | 0/4 | 0/4 | 4/4 | 0/4 |
| 0 | W8 | 0/4 | 0/4 | 4/4 | 0/4 |
| 1 | W0 | 0/4 | 0/4 | 4/4 | 0/4 |
| 1 | W8 | 0/4 | 0/4 | 4/4 | 0/4 |
| 2 | W0 | 0/4 | 0/4 | 4/4 | 0/4 |
| 2 | W8 | 0/4 | 0/4 | 4/4 | 0/4 |

This is **one authenticated eight-EVENT source bank** and three optimization
realizations. It is not three independent worlds, twelve independent learned
facts, or population evidence. The positive cells are the same four A facts
read under two prompt surfaces after three optimizer/dropout seeds.

The exact defensible claim is:

> On one exposed, format-assisted DEV EVENT bank, the all-layer rank-8 A200
> writer made four A-bank rows exactly available from LoRA weights after 200
> updates, across three optimizer/dropout seeds and an exposed paraphrased
> read surface, while the frozen base and the four untrained B rows remained
> 0/4.

Do not shorten this to “retention works” or “the agent learned from its life.”
SEQ-194 did not write B, revisit A after a B write, compose memories, choose a
memory cue, or improve an action.

## What I checked independently

### 1. Raw outputs, not saved aggregate scores

For every seed and both states, I joined the 16 captured generations to the
eight exact targets in the pinned material. All 48 C0 generations differed
from their targets. In each A200 state, exactly the eight A generations (four
at W0 and four at W8) were byte-for-byte equal to their target including the
terminal LF; every B generation differed. All 96 readout calls had
`finish_reason=stop`; none had `finish_reason=length`.

The reducer itself is also appropriately strict. It rereads every raw actor
capture, reconstructs its request and frozen sampling record, recomputes the
EVENT score, requires a normal stop, rejoins the mounted adapter bytes to the
fit checkpoint, and accepts no caller-provided pass Boolean or answer repair.

W8 is only a paraphrased request wrapper over the same singleton address and
target. W0--W7 appeared in training; W8 did not, but its wording and bank are
exposed DEV. Thus W8 is useful interface robustness, not unseen-fact
generalization or confirmation data.

### 2. One bank, three learner seeds

The canonical `.spec.records` projection has the same SHA-256 in all three
materials:

`b756159909cfd8f2c0892e745191ef5a850fc7fb02731171b0eacb95aa80c768`

All three also bind the same imported evidence
`cc9e97a290933633d67c371625ae5cfffeb46bc8ca7c130279022868e98a545e`,
the same v1 spec
`58cd77d23bf57d6e7336ecdcc87c9a5b32fc2ae5d705b7a49ae11dd65a6569b8`,
the same A200 item hash
`fa4f697558d706b9b3e9d48c5bd58f968a1336b2d57c0a44df77d12e36532cda`,
and the same encoding hash
`514a0791e3bf56b8a2dfdb04ea035b15354465bcbf923eaf8e70cff418701898`.
Only the declared learner seed and resulting adapter/spec/export identities
differ.

The eight imported records are marked `CHILD_NATIVE`, retain their original
capture hashes, and are ordered A4 then B4. The source history also correctly
records that the original wider formation attempt failed. That history is not
converted into a successful formation or own-action claim by this writer
screen.

### 3. Exact writer dose and checkpoint binding

Each seed started from fresh C0 and used:

- Qwen2.5-7B-Instruct revision
  `a09a35458c702b33eeacc393d103063234e8bc28`;
- all-layer LoRA over q/k/v/o and gate/up/down projections;
- rank 8, alpha 16, dropout 0.05, bf16, AdamW, LR `3e-5`;
- batch 4, 200 optimizer updates, 800 A-only presentations;
- 114,200 training input tokens and 42,000 supervised target tokens;
- no packing, no training truncation, no skipped targets, and no nonfinite
  batches.

Every A fact therefore appeared 200 times across the eight W0--W7 variants.
Across all three learner seeds the run used exactly three fits, 600 updates,
2,400 presentations, and 96 cold readout calls (16 C0 plus 16 A200 per seed).
No B row entered an A200 corpus; each corpus was exactly 800 A rows and zero B
rows.

Each fit receipt binds a fresh-C0 parent (`parent_phase=null`,
`predecessor=null`, `warm_start=null`), reports the frozen base unchanged, and
binds the exact 80,792,096-byte adapter checkpoint later copied into its A200
reader. Adapter model hashes are distinct as expected across learner seeds:

- seed 0:
  `ac5405eddb5856f19b1db9025b692e781da7b88dd909938a37fcf784c99156a7`;
- seed 1:
  `c3f9dd87888cbb3822c6b81df00ae9da52dae21386f845c804073e8c198f9ba4`;
- seed 2:
  `01fb42dd9bf712c3cb856ac96f7faaf79a42d25be987a601dfca38d1404b202f`.

The model inventory matches the public Qwen revision and the CPU base-state
receipt binds bf16 tensor-state SHA-256
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
The prospective model-binding receipt explicitly says
`clean_lineage_certified=false`; therefore this DEV result must not be reused
as a clean-lineage or final-paper attestation.

### 4. Immutable artifact and source custody

The campaign manifest file independently hashes to its launch pin:

`4e41adf04873a5f119f2f372dcb6ab27c561134c8ff7f407e72ec6b242d89731`.

I recomputed all 17 manifest source-file hashes: 17/17 match. I recursively
recomputed every exact `{path, sha256}` pin in each reducer receipt: 11/11 per
seed, 33/33 total, match. I then recomputed the size and SHA-256 of every file
listed in all nine outer collections: 747/747 match, including raw requests,
raw responses, scores, checkpoint files, process receipts, and fit/readout
completion records.

The three reducer receipt **file** hashes are:

- seed 0:
  `045aaf1b99cf714752ccc4ce015f570bb0fc803539a61af7eabc5436ad42c0ea`;
- seed 1:
  `3b0efc7272d83d41e8bc238d35df1f32e151bf90ff055e9f7a84820321ef0cf5`;
- seed 2:
  `a2e14c6d68e7e3fe2de8d8e5093aa5dd9d2f7e50263dc35a7c755f8ce03fb6bd`.

No pin or inventory mismatch was found.

### 5. Release and terminality

The controller PID 233271 finished at
`2026-09-13T19:15:20.576734+00:00` with all nine stages marked completed and
released. Each fit, C0 readout, and A200 readout records return code 0, no
errors, no retry, an empty post-stage GPU owner list, a clear post-stage CVD
scope, and an empty released process group. A fresh process check found none
of the controller or recorded workers alive and no matching SEQ-194 process
or GPU allocation.

## P-CHAIN-2 prerequisite

**The explicitly named P-CHAIN-2 A200 acquisition prerequisite is met.** The
result does not disqualify the frozen core writer tuple, and it positively
shows that this rank/capacity/heat recipe can install exact opaque relations
in the EVENT serialization. P-CHAIN-2 may advance only through its remaining
already-bound gates, especially fresh source audit and its own material,
tokenization, LR0, and shortcut checks.

This opening is procedural, not predictive. P-CHAIN-2 uses a different
chat-templated `MEMORY NEXT` serialization and asks for two-hop composition;
SEQ-194 used non-chat-template format-assisted EVENT rows and singleton reads.
Accordingly, SEQ-194 does **not** establish that P-CHAIN atoms will acquire or
compose. Its first P-CHAIN fit/readout remains an actual scientific test, not a
formality.

## What remains unproved

- retention of A after a later B write;
- coexistence of A and B in one descendant adapter;
- replay benefit versus fixed-work or clean cumulative controls;
- autonomous acquisition, cueing, connection, composition, or action use;
- unseen-fact or unseen-bank generalization;
- parenting, lifetime improvement, H1/H2, C11, or whole-organism claims;
- statistical replication over independent fact banks or worlds.

Those questions begin with the still-separate descendant retention campaign
and P-CHAIN-2. SEQ-194 closes only their writer-acquisition prerequisite.
