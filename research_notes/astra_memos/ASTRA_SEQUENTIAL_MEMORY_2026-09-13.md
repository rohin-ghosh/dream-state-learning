# SEQ-118 — two sequential new-memory cycles, seed 0

**COMPLETE; source-bound terminal collection and independent raw review PASS.
Exploratory fixed-budget allocation result, not parenting or general
G3 qualification.**

The two trajectories start from the same completed seed-0 FOUR_VIEW adapter
at 400 cumulative updates. Each receives two successive 320-update fits on
new, disjoint 16-fact banks, continuing its own preceding weights with a
fresh seed-0 optimizer. Cumulative updates are 400 → 720 → 1040. R spends part
of its fixed budget replaying old facts; NEW_ONLY spends those slots on more
current facts. Arithmetic anchors are identical. This is **not new-dose-matched**:
R presents each current fact 20 times per cycle versus NEW_ONLY's 40.

## Stored outcomes

Entries are correct facts on development/exact surfaces, each out of 16.
The two surfaces are repeated probes of the same facts, not independent facts.
Arithmetic columns each have 32 cases. All 640 requests were captured before
any reduction; Main inspected only blind status before terminal collection.

| State | Old M0 dev/exact | B1 dev/exact | B2 dev/exact | Arithmetic adherence | Correct ACT |
|---|---:|---:|---:|---:|---:|
| S0 |16/16|5/5|7/6|32|32|
| R1 |16/16|16/16|5/6|32|32|
| NEW_ONLY1 |10/8|16/16|5/4|32|32|
| R2 |16/16|16/16|16/16|32|32|
| NEW_ONLY2 |9/8|4/4|16/16|32|32|

All memory outputs are valid under the frozen scorer. R retains the original
bank while acquiring B1, then retains both old banks while acquiring B2.
NEW_ONLY acquires both new banks when trained, but loses old-bank accuracy;
B1 was fully acquired at its own cycle-1 checkpoint, so its cycle-2 decline
is a retention failure rather than merely unequal initial acquisition.
Arithmetic interface adherence and numerical correctness remain intact in
both trajectories. Independent per-fact auditing confirms twelve B1 facts fail
on both surfaces after NEW_ONLY2. Its unchanged M0 exact total between cycles
hides four recoveries and four new failures, rather than an unchanged set of
remembered answers. All 640 outputs stop normally, with no token-cap hits.

Under the prospectively frozen watcher matrix, R is safe integration and
NEW_ONLY is old forgetting with new acquisition. This supports the practical
replay allocation at this load and seed. It does not isolate replay from lower
new-content dose, batch composition, or their interaction. It does not establish
general repeated-learning stability, a learned extraction policy, clean ancestry,
parenting, or H1/H2. No automatic mechanism freeze or new fits are authorized by
the numerical result itself. The matrix is
`research_notes/analysis/2026-09-12_sequential_old_new_fixed_budget_prospective_outcome_matrix.md`.

## Reproduction and custody

- Source commit: `5a1f300fed4b7f1ef54524869c2bf11509e965ca`.
- Native root: `~/astra_diagnostics/astra_sequential_memory_20260912_attempt2/seed0_pair_attempt2`.
- Plan SHA256: `9e53c716373c2458586ff7b6a72d0fe5822d41d5a0129057e2a4e805acab8b49`.
- Driver SHA256: `29d70e46f0c65817f65f52f6ed310fcfaa91cda64928f9bdfc54b70834a0c232`.
- Former node-3 GPU-0 controller/PGID: 263983, launched September 12 at
  23:35:40.672863 UTC. Terminal COMPLETE; collection checked controller absence,
  full GPU/process/queue vacancy, pinned inputs, saved supervision and artifacts.
- Capsule: `receipts_20260912/astra_sequential_memory_seed0_pair_attempt2_terminal_20260913T0000Z.tgz`.
  SHA256 `c63437c47918603d5b784544bcae85e7febc93ec7516677eaa9a3608b78b2fb0`;
  1,421 checked metadata members. Its separately archived `.validation.json`
  binds every member. Weights remain on the native node, not in this capsule.
- Controller reservation 1,295.975722 seconds; workers 1,181.033689 seconds;
  observed full reservation to vacancy 1,327.460648 seconds (22.124344 A40-min).
  These intervals overlap and must not be added. Packaging follows vacancy;
  collection's final check remained within the 90-minute global bound.
- Collector ran once, without native model/tokenizer or reducer reruns. Main
  received an exact capsule hash match. No Main signals or kills occurred.
- Herschel independently scored all 640 raw calls with zero discrepancies;
  review SHA256 `7717ce3eec75634e7ca9eba97bc601c664e30f1708f7b389f5baae4e7bc77434`.
  Its additive custody supplement verifies the subsequently supplied external
  validation and all 1,421 member hashes. It does not supply an otherwise
  absent final-packaging timestamp. Both reviews and raw analysis are archived.
  Native weights, execution and model origin remain receipt-backed rather than
  independently remeasured. No additional scientific promotion follows.

Stored counts can be reproduced without a model:

```bash
tar -xOf research_notes/astra_memos/receipts_20260912/astra_sequential_memory_seed0_pair_attempt2_terminal_20260913T0000Z.tgz \
  seed0_pair_attempt2/run/terminal.json | jq '.reductions | map_values(.counts)'
```

## Next decision and revised priority

Rohin's raw message 23 prioritizes level-1 birth from a sourced ideal corpus,
then sampling level-2 teaching on that born learner. Main accepts this steer
within the existing optional birth-adapter authorization. Birth is not itself
evidence that parenting works; high plasticity and corpus quality are hypotheses
to measure, not labels that certify success.

Accordingly, the prepared fresh-base process FIT-seed-0/1 replications remain
**UNLAUNCHED**, not failed or completed. Their runner passes 27 Main/native
tests, collectors 19 Main/native tests, and both native material preparations
pass. Their preserved plans are respectively
`ff6bbf2834cc300e9e5cb6ec1f36975bc4d7dd1ae29c1bb4936ce887d7fdb43d`
and `a761747b53b43cd62ab664884419838c9f7b60b8df9ee0b7cd51b57230a428d9`.
No dose change or claim rescue is inferred from their deferral.

The immediate birth diagnostic keeps valid PROSPECT material, repairs the
SEQ-108 REVISE EXPECTED-factor shortcut, and adds truthful locality anchors.
Its independent authored-map control, held-out conditional flips and unrelated
interface tests precede any parent-free level-2 utility interpretation. Existing
corpora and failed locality evidence remain unchanged. Formal C11 guard remains
deferred; provenance/quarantine and simple operational hygiene remain active.
